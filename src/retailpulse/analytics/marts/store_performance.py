from psycopg import Connection


def refresh_store_performance(
    connection: Connection,
) -> int:
    """
    Refresh the store performance analytical mart.

    Grain:
        One row per store.

    Order-level financial metrics and item-level
    quantity metrics are aggregated separately to
    prevent fact-to-fact fan-out.
    """

    with connection.transaction(), connection.cursor() as cursor:

        # -------------------------------------------------
        # Remove previous mart contents
        # -------------------------------------------------

        cursor.execute(
            """
                DELETE FROM
                    analytics.mart_store_performance
                """
        )

        # -------------------------------------------------
        # Build store-level metrics
        # -------------------------------------------------

        cursor.execute(
            """
                WITH order_metrics AS (

                    SELECT
                        fo.store_key,

                        COUNT(
                            DISTINCT fo.order_key
                        ) AS order_count,

                        SUM(
                            fo.subtotal_amount
                        ) AS gross_sales,

                        SUM(
                            fo.discount_amount
                        ) AS discount_amount,

                        SUM(
                            fo.tax_amount
                        ) AS tax_amount,

                        SUM(
                            fo.total_amount
                        ) AS net_sales,

                        MIN(
                            d.full_date
                        ) AS first_order_date,

                        MAX(
                            d.full_date
                        ) AS last_order_date

                    FROM analytics.fact_order fo

                    JOIN analytics.dim_date d
                        ON d.date_key =
                           fo.order_date_key

                    WHERE fo.store_key IS NOT NULL

                    GROUP BY
                        fo.store_key
                ),

                item_metrics AS (

                    SELECT
                        fo.store_key,

                        SUM(
                            foi.quantity
                        ) AS units_sold

                    FROM analytics.fact_order fo

                    JOIN analytics.fact_order_item foi
                        ON foi.order_key =
                           fo.order_key

                    WHERE fo.store_key IS NOT NULL

                    GROUP BY
                        fo.store_key
                ),

                store_metrics AS (

                    SELECT
                        o.store_key,

                        o.order_count,

                        COALESCE(
                            i.units_sold,
                            0
                        ) AS units_sold,

                        o.gross_sales,

                        o.discount_amount,

                        o.tax_amount,

                        o.net_sales,

                        CASE
                            WHEN o.order_count > 0
                            THEN
                                o.net_sales
                                / o.order_count
                            ELSE 0
                        END AS average_order_value,

                        o.first_order_date,

                        o.last_order_date

                    FROM order_metrics o

                    LEFT JOIN item_metrics i
                        ON i.store_key =
                           o.store_key
                ),

                ranked_stores AS (

                    SELECT
                        store_key,

                        order_count,

                        units_sold,

                        gross_sales,

                        discount_amount,

                        tax_amount,

                        net_sales,

                        average_order_value,

                        first_order_date,

                        last_order_date,

                        RANK() OVER (
                            ORDER BY
                                net_sales DESC
                        ) AS store_rank

                    FROM store_metrics
                )

                INSERT INTO
                    analytics.mart_store_performance (
                        store_key,
                        store_id,
                        store_code,
                        store_name,
                        city,
                        state,
                        country_code,
                        region,
                        store_type,
                        order_count,
                        units_sold,
                        gross_sales,
                        discount_amount,
                        tax_amount,
                        net_sales,
                        average_order_value,
                        first_order_date,
                        last_order_date,
                        store_rank
                    )

                SELECT
                    rs.store_key,

                    ds.store_id,

                    ds.store_code,

                    ds.store_name,

                    ds.city,

                    ds.state,

                    ds.country_code,

                    ds.region,

                    ds.store_type,

                    rs.order_count,

                    rs.units_sold,

                    rs.gross_sales,

                    rs.discount_amount,

                    rs.tax_amount,

                    rs.net_sales,

                    rs.average_order_value,

                    rs.first_order_date,

                    rs.last_order_date,

                    rs.store_rank

                FROM ranked_stores rs

                JOIN analytics.dim_store ds
                    ON ds.store_key =
                       rs.store_key
                """
        )

        # -------------------------------------------------
        # Refresh timestamp
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE
                    analytics.mart_store_performance
                SET refreshed_at =
                    CURRENT_TIMESTAMP
                """
        )

        return cursor.rowcount
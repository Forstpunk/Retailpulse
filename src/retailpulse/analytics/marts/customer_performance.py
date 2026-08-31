from psycopg import Connection


def refresh_customer_performance(
    connection: Connection,
) -> int:
    """
    Refresh the customer performance analytical mart.

    Grain:
        One row per customer.

    Order-level financial metrics are calculated
    independently from item-level quantity metrics
    to prevent fact-to-fact fan-out.
    """

    with connection.transaction(), connection.cursor() as cursor:

        # -------------------------------------------------
        # Remove previous mart contents
        # -------------------------------------------------

        cursor.execute(
            """
                DELETE FROM
                    analytics.mart_customer_performance
                """
        )

        # -------------------------------------------------
        # Build customer-level metrics
        #
        # Keep order and item aggregations separate.
        # -------------------------------------------------

        cursor.execute(
            """
                WITH order_metrics AS (

                    SELECT
                        fo.customer_key,

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

                    GROUP BY
                        fo.customer_key
                ),

                item_metrics AS (

                    SELECT
                        fo.customer_key,

                        SUM(
                            foi.quantity
                        ) AS units_purchased

                    FROM analytics.fact_order fo

                    JOIN analytics.fact_order_item foi
                        ON foi.order_key =
                           fo.order_key

                    GROUP BY
                        fo.customer_key
                ),

                customer_metrics AS (

                    SELECT
                        o.customer_key,

                        o.order_count,

                        COALESCE(
                            i.units_purchased,
                            0
                        ) AS units_purchased,

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
                        ON i.customer_key =
                           o.customer_key
                ),

                ranked_customers AS (

                    SELECT
                        customer_key,

                        order_count,

                        units_purchased,

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
                        ) AS customer_rank

                    FROM customer_metrics
                )

                INSERT INTO
                    analytics.mart_customer_performance (
                        customer_key,
                        customer_id,
                        customer_number,
                        first_name,
                        last_name,
                        customer_segment,
                        city,
                        state,
                        country_code,
                        order_count,
                        units_purchased,
                        gross_sales,
                        discount_amount,
                        tax_amount,
                        net_sales,
                        average_order_value,
                        first_order_date,
                        last_order_date,
                        customer_rank
                    )

                SELECT
                    rc.customer_key,

                    dc.customer_id,

                    dc.customer_number,

                    dc.first_name,

                    dc.last_name,

                    dc.customer_segment,

                    dc.city,

                    dc.state,

                    dc.country_code,

                    rc.order_count,

                    rc.units_purchased,

                    rc.gross_sales,

                    rc.discount_amount,

                    rc.tax_amount,

                    rc.net_sales,

                    rc.average_order_value,

                    rc.first_order_date,

                    rc.last_order_date,

                    rc.customer_rank

                FROM ranked_customers rc

                JOIN analytics.dim_customer dc
                    ON dc.customer_key =
                       rc.customer_key
                """
        )

        # -------------------------------------------------
        # Refresh timestamp
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE
                    analytics.mart_customer_performance
                SET refreshed_at =
                    CURRENT_TIMESTAMP
                """
        )

        return cursor.rowcount
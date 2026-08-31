from psycopg import Connection


def refresh_daily_sales(
    connection: Connection,
) -> int:
    """
    Refresh the daily sales analytical mart.

    Grain:
        One row per calendar date.

    Order-level metrics are calculated separately
    from item-level metrics to avoid fan-out
    aggregation.
    """

    with connection.transaction(), connection.cursor() as cursor:

        # -------------------------------------------------
        # Remove previous mart contents
        # -------------------------------------------------

        cursor.execute(
            """
                DELETE FROM analytics.mart_daily_sales
                """
        )

        # -------------------------------------------------
        # Rebuild daily aggregates
        # -------------------------------------------------

        cursor.execute(
            """
                WITH order_daily AS (

                    SELECT
                        fo.order_date_key AS date_key,

                        COUNT(*) AS order_count,

                        SUM(
                            fo.total_amount
                        ) AS net_sales,

                        SUM(
                            fo.shipping_amount
                        ) AS shipping_amount

                    FROM analytics.fact_order fo

                    GROUP BY
                        fo.order_date_key
                ),

                item_daily AS (

                    SELECT
                        fo.order_date_key AS date_key,

                        COUNT(
                            foi.order_item_key
                        ) AS order_item_count,

                        COALESCE(
                            SUM(
                                foi.quantity
                            ),
                            0
                        ) AS units_sold,

                        COALESCE(
                            SUM(
                                foi.quantity
                                * foi.unit_price
                            ),
                            0
                        ) AS gross_sales,

                        COALESCE(
                            SUM(
                                foi.discount_amount
                            ),
                            0
                        ) AS discount_amount,

                        COALESCE(
                            SUM(
                                foi.tax_amount
                            ),
                            0
                        ) AS tax_amount,

                        COALESCE(
                            SUM(
                                foi.line_total
                            ),
                            0
                        ) AS item_net_sales

                    FROM analytics.fact_order_item foi

                    JOIN analytics.fact_order fo
                        ON fo.order_key =
                           foi.order_key

                    GROUP BY
                        fo.order_date_key
                )

                INSERT INTO analytics.mart_daily_sales (
                    date_key,
                    order_count,
                    order_item_count,
                    units_sold,
                    gross_sales,
                    discount_amount,
                    tax_amount,
                    shipping_amount,
                    net_sales,
                    average_order_value
                )

                SELECT
                    d.date_key,

                    o.order_count,

                    i.order_item_count,

                    i.units_sold,

                    i.gross_sales,

                    i.discount_amount,

                    i.tax_amount,

                    o.shipping_amount,

                    o.net_sales,

                    CASE
                        WHEN o.order_count > 0
                        THEN
                            o.net_sales
                            / o.order_count
                        ELSE 0
                    END AS average_order_value

                FROM order_daily o

                JOIN item_daily i
                    ON i.date_key = o.date_key

                JOIN analytics.dim_date d
                    ON d.date_key = o.date_key
                """
        )

        # -------------------------------------------------
        # Update refresh timestamp
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE analytics.mart_daily_sales
                SET refreshed_at =
                    CURRENT_TIMESTAMP
                """
        )

        return cursor.rowcount
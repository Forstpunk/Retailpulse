from psycopg import Connection


def refresh_product_performance(
    connection: Connection,
) -> int:
    """
    Refresh the product performance analytical mart.

    Grain:
        One row per product.

    Measures are derived from fact_order_item.
    Product attributes come from dim_product.
    """

    with connection.transaction(), connection.cursor() as cursor:

        # -------------------------------------------------
        # Remove previous results
        # -------------------------------------------------

        cursor.execute(
            """
                DELETE FROM
                    analytics.mart_product_performance
                """
        )

        # -------------------------------------------------
        # Aggregate product performance
        # -------------------------------------------------

        cursor.execute(
            """
                WITH product_metrics AS (

                    SELECT
                        foi.product_key,

                        COUNT(
                            DISTINCT fo.order_key
                        ) AS order_count,

                        SUM(
                            foi.quantity
                        ) AS units_sold,

                        SUM(
                            foi.quantity
                            * foi.unit_price
                        ) AS gross_sales,

                        SUM(
                            foi.discount_amount
                        ) AS discount_amount,

                        SUM(
                            foi.tax_amount
                        ) AS tax_amount,

                        SUM(
                            foi.line_total
                        ) AS net_sales,

                        CASE
                            WHEN SUM(
                                foi.quantity
                            ) > 0
                            THEN
                                SUM(
                                    foi.quantity
                                    * foi.unit_price
                                )
                                /
                                SUM(
                                    foi.quantity
                                )
                            ELSE 0
                        END AS average_unit_price

                    FROM analytics.fact_order_item foi

                    JOIN analytics.fact_order fo
                        ON fo.order_key =
                           foi.order_key

                    GROUP BY
                        foi.product_key
                ),

                ranked_products AS (

                    SELECT
                        product_key,

                        order_count,

                        units_sold,

                        gross_sales,

                        discount_amount,

                        tax_amount,

                        net_sales,

                        average_unit_price,

                        CASE
                            WHEN gross_sales > 0
                            THEN
                                discount_amount
                                / gross_sales
                            ELSE 0
                        END AS discount_rate,

                        RANK() OVER (
                            ORDER BY
                                net_sales DESC
                        ) AS sales_rank

                    FROM product_metrics
                )

                INSERT INTO
                    analytics.mart_product_performance (
                        product_key,
                        product_id,
                        sku,
                        product_name,
                        category_key,
                        supplier_key,
                        order_count,
                        units_sold,
                        gross_sales,
                        discount_amount,
                        tax_amount,
                        net_sales,
                        average_unit_price,
                        discount_rate,
                        sales_rank
                    )

                SELECT
                    rp.product_key,

                    dp.product_id,

                    dp.sku,

                    dp.product_name,

                    dp.category_id,

                    dp.supplier_id,

                    rp.order_count,

                    rp.units_sold,

                    rp.gross_sales,

                    rp.discount_amount,

                    rp.tax_amount,

                    rp.net_sales,

                    rp.average_unit_price,

                    rp.discount_rate,

                    rp.sales_rank

                FROM ranked_products rp

                JOIN analytics.dim_product dp
                    ON dp.product_key =
                       rp.product_key
                """
        )

        # -------------------------------------------------
        # Refresh timestamp
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE analytics.mart_product_performance
                SET refreshed_at =
                    CURRENT_TIMESTAMP
                """
        )

        return cursor.rowcount
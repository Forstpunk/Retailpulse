from collections.abc import Iterable

from psycopg import Connection

from retailpulse.analytics.models.product import (
    SourceProduct,
)


def load_products(
    connection: Connection,
    products: Iterable[SourceProduct],
) -> int:
    """
    Upsert source products into analytics.dim_product via
    a bulk COPY + set-based upsert rather than one round
    trip per row — see order_fact_loader for why that
    matters at RetailPulse's data volumes.

    category_id/supplier_id are carried through as plain
    business-key columns (dim_product has no surrogate
    category_key/supplier_key), so no dimension-key
    resolution is needed here.

    Existing products are updated only when the source
    record has a newer source_updated_at timestamp.

    Returns
    -------
    int
        Number of products processed.
    """

    products = list(products)

    if not products:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_dim_product_staging (
                        product_id BIGINT,
                        sku VARCHAR(50),
                        product_name VARCHAR(255),
                        category_id BIGINT,
                        supplier_id BIGINT,
                        unit_price NUMERIC(12,2),
                        cost_price NUMERIC(12,2),
                        status VARCHAR(30),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_dim_product_staging"
        )

        with cursor.copy(
            """
                COPY tmp_dim_product_staging (
                    product_id,
                    sku,
                    product_name,
                    category_id,
                    supplier_id,
                    unit_price,
                    cost_price,
                    status,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for product in products:

                copy.write_row(
                    (
                        product.product_id,
                        product.sku,
                        product.product_name,
                        product.category_id,
                        product.supplier_id,
                        product.unit_price,
                        product.cost_price,
                        product.status,
                        product.created_at,
                        product.updated_at,
                    )
                )

        cursor.execute(
            """
                INSERT INTO analytics.dim_product (
                    product_id,
                    sku,
                    product_name,
                    category_id,
                    supplier_id,
                    unit_price,
                    cost_price,
                    status,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    product_id,
                    sku,
                    product_name,
                    category_id,
                    supplier_id,
                    unit_price,
                    cost_price,
                    status,
                    source_created_at,
                    source_updated_at
                FROM tmp_dim_product_staging
                ON CONFLICT (product_id)
                DO UPDATE
                SET
                    sku =
                        EXCLUDED.sku,
                    product_name =
                        EXCLUDED.product_name,
                    category_id =
                        EXCLUDED.category_id,
                    supplier_id =
                        EXCLUDED.supplier_id,
                    unit_price =
                        EXCLUDED.unit_price,
                    cost_price =
                        EXCLUDED.cost_price,
                    status =
                        EXCLUDED.status,
                    source_created_at =
                        EXCLUDED.source_created_at,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.dim_product.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(products)

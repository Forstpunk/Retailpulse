from psycopg import Connection

from retailpulse.analytics.repositories.supplier_repository import (
    SourceSupplier,
)


def load_suppliers(
    connection: Connection,
    suppliers: list[SourceSupplier],
) -> int:
    """
    Upsert source suppliers into analytics.dim_supplier
    via a bulk COPY + set-based upsert rather than one
    round trip per row — see order_fact_loader for why
    that matters at RetailPulse's data volumes.
    """

    if not suppliers:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_dim_supplier_staging (
                        supplier_id BIGINT,
                        supplier_name VARCHAR(200),
                        country_code CHAR(2),
                        status VARCHAR(30),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_dim_supplier_staging"
        )

        with cursor.copy(
            """
                COPY tmp_dim_supplier_staging (
                    supplier_id,
                    supplier_name,
                    country_code,
                    status,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for supplier in suppliers:

                copy.write_row(
                    (
                        supplier.supplier_id,
                        supplier.supplier_name,
                        supplier.country_code,
                        supplier.status,
                        supplier.created_at,
                        supplier.updated_at,
                    )
                )

        cursor.execute(
            """
                INSERT INTO analytics.dim_supplier (
                    supplier_id,
                    supplier_name,
                    country_code,
                    status,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    supplier_id,
                    supplier_name,
                    country_code,
                    status,
                    source_created_at,
                    source_updated_at
                FROM tmp_dim_supplier_staging
                ON CONFLICT (supplier_id)
                DO UPDATE SET
                    supplier_name =
                        EXCLUDED.supplier_name,
                    country_code =
                        EXCLUDED.country_code,
                    status =
                        EXCLUDED.status,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.dim_supplier.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(suppliers)

from collections.abc import Iterable

from psycopg import Connection

from retailpulse.analytics.models.store import (
    SourceStore,
)


def load_stores(
    connection: Connection,
    stores: Iterable[SourceStore],
) -> int:
    """
    Upsert source stores into analytics.dim_store via a
    bulk COPY + set-based upsert rather than one round
    trip per row — see order_fact_loader for why that
    matters at RetailPulse's data volumes.

    Existing stores are updated only when the source
    record has a newer source_updated_at timestamp.

    Returns
    -------
    int
        Number of stores processed.
    """

    stores = list(stores)

    if not stores:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_dim_store_staging (
                        store_id BIGINT,
                        store_code VARCHAR(30),
                        store_name VARCHAR(200),
                        city VARCHAR(100),
                        state VARCHAR(100),
                        country_code CHAR(2),
                        region VARCHAR(100),
                        store_type VARCHAR(50),
                        opened_date DATE,
                        status VARCHAR(30),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_dim_store_staging"
        )

        with cursor.copy(
            """
                COPY tmp_dim_store_staging (
                    store_id,
                    store_code,
                    store_name,
                    city,
                    state,
                    country_code,
                    region,
                    store_type,
                    opened_date,
                    status,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for store in stores:

                copy.write_row(
                    (
                        store.store_id,
                        store.store_code,
                        store.store_name,
                        store.city,
                        store.state,
                        store.country_code,
                        store.region,
                        store.store_type,
                        store.opened_date,
                        store.status,
                        store.created_at,
                        store.updated_at,
                    )
                )

        cursor.execute(
            """
                INSERT INTO analytics.dim_store (
                    store_id,
                    store_code,
                    store_name,
                    city,
                    state,
                    country_code,
                    region,
                    store_type,
                    opened_date,
                    status,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    store_id,
                    store_code,
                    store_name,
                    city,
                    state,
                    country_code,
                    region,
                    store_type,
                    opened_date,
                    status,
                    source_created_at,
                    source_updated_at
                FROM tmp_dim_store_staging
                ON CONFLICT (store_id)
                DO UPDATE
                SET
                    store_code =
                        EXCLUDED.store_code,
                    store_name =
                        EXCLUDED.store_name,
                    city =
                        EXCLUDED.city,
                    state =
                        EXCLUDED.state,
                    country_code =
                        EXCLUDED.country_code,
                    region =
                        EXCLUDED.region,
                    store_type =
                        EXCLUDED.store_type,
                    opened_date =
                        EXCLUDED.opened_date,
                    status =
                        EXCLUDED.status,
                    source_created_at =
                        EXCLUDED.source_created_at,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.dim_store.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(stores)

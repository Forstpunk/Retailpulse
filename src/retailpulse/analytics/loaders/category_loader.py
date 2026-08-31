from psycopg import Connection

from retailpulse.analytics.repositories.category_repository import (
    SourceCategory,
)


def load_categories(
    connection: Connection,
    categories: list[SourceCategory],
) -> int:
    """
    Upsert source categories into analytics.dim_category
    via a bulk COPY + set-based upsert rather than one
    round trip per row — see order_fact_loader for why
    that matters at RetailPulse's data volumes.
    """

    if not categories:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_dim_category_staging (
                        category_id BIGINT,
                        category_name VARCHAR(100),
                        parent_category_id BIGINT,
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        # IF NOT EXISTS + TRUNCATE, not a bare CREATE: if this
        # stage is retried within the same still-open
        # transaction (no COMMIT in between, so ON COMMIT DROP
        # hasn't fired), a bare CREATE would fail with
        # "already exists" on the second attempt.
        cursor.execute(
            "TRUNCATE TABLE tmp_dim_category_staging"
        )

        with cursor.copy(
            """
                COPY tmp_dim_category_staging (
                    category_id,
                    category_name,
                    parent_category_id,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for category in categories:

                copy.write_row(
                    (
                        category.category_id,
                        category.category_name,
                        category.parent_category_id,
                        category.created_at,
                        category.updated_at,
                    )
                )

        cursor.execute(
            """
                INSERT INTO analytics.dim_category (
                    category_id,
                    category_name,
                    parent_category_id,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    category_id,
                    category_name,
                    parent_category_id,
                    source_created_at,
                    source_updated_at
                FROM tmp_dim_category_staging
                ON CONFLICT (category_id)
                DO UPDATE SET
                    category_name =
                        EXCLUDED.category_name,
                    parent_category_id =
                        EXCLUDED.parent_category_id,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.dim_category.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(categories)

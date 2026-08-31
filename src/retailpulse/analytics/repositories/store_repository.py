from psycopg import Connection

from retailpulse.analytics.models.store import (
    SourceStore,
)


def get_stores(
    connection: Connection,
) -> list[SourceStore]:
    """
    Read stores from the retail source schema.

    This repository is read-only.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
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
                created_at,
                updated_at
            FROM retail.stores
            ORDER BY store_id
            """
        )

        rows = cursor.fetchall()

    return [
        SourceStore(
            store_id=row[0],
            store_code=row[1],
            store_name=row[2],
            city=row[3],
            state=row[4],
            country_code=row[5],
            region=row[6],
            store_type=row[7],
            opened_date=row[8],
            status=row[9],
            created_at=row[10],
            updated_at=row[11],
        )
        for row in rows
    ]
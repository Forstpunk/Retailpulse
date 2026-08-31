from uuid import UUID

from psycopg import Connection


def try_start_batch(
    connection: Connection,
    batch_id: UUID,
    source_system: str,
    batch_type: str,
) -> bool:
    """
    Atomically claim an ingestion batch.

    Returns:
        True  -> newly claimed batch
        False -> batch already exists
    """

    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO retail.ingestion_batches (
                    batch_id,
                    source_system,
                    batch_type,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'STARTED'
                )
                ON CONFLICT (batch_id)
                DO NOTHING
                """,
            (
                batch_id,
                source_system,
                batch_type,
            ),
        )

        return cursor.rowcount == 1
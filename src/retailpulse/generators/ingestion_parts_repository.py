from uuid import UUID

from psycopg import Connection


def start_batch_part(
    connection: Connection,
    *,
    batch_id: UUID,
    part_number: int,
    start_order_id: int,
    start_order_item_id: int,
) -> bool:
    """
    Start a physical ingestion batch part.

    The STARTED checkpoint is committed independently
    before the physical batch is processed.

    Returns
    -------
    bool
        True:
            The part needs to be processed.

        False:
            The part has already completed successfully.
    """

    if part_number <= 0:
        raise ValueError(
            "part_number must be greater than zero"
        )

    if start_order_id <= 0:
        raise ValueError(
            "start_order_id must be greater than zero"
        )

    if start_order_item_id <= 0:
        raise ValueError(
            "start_order_item_id must be greater than zero"
        )

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                SELECT status
                FROM retail.ingestion_batch_parts
                WHERE
                    batch_id = %s
                    AND part_number = %s
                """,
            (
                batch_id,
                part_number,
            ),
        )

        existing = cursor.fetchone()

        # -------------------------------------------------
        # Existing physical part
        # -------------------------------------------------

        if existing is not None:

            status = existing[0]

            # Already completed.
            if status == "COMPLETED":
                return False

            # FAILED or STARTED.
            # Reclaim the physical part.
            cursor.execute(
                """
                    UPDATE retail.ingestion_batch_parts
                    SET
                        status = 'STARTED',
                        start_order_id = %s,
                        start_order_item_id = %s,
                        started_at = CURRENT_TIMESTAMP,
                        completed_at = NULL,
                        error_message = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE
                        batch_id = %s
                        AND part_number = %s
                    """,
                (
                    start_order_id,
                    start_order_item_id,
                    batch_id,
                    part_number,
                ),
            )

            return True

        # -------------------------------------------------
        # First attempt
        # -------------------------------------------------

        cursor.execute(
            """
                INSERT INTO retail.ingestion_batch_parts (
                    batch_id,
                    part_number,
                    status,
                    start_order_id,
                    start_order_item_id
                )
                VALUES (
                    %s,
                    %s,
                    'STARTED',
                    %s,
                    %s
                )
                """,
            (
                batch_id,
                part_number,
                start_order_id,
                start_order_item_id,
            ),
        )

        return True


def complete_batch_part(
    connection: Connection,
    *,
    batch_id: UUID,
    part_number: int,
    record_count: int,
    order_item_count: int,
) -> None:
    """
    Mark a physical batch part as completed.

    The caller owns the transaction boundary.
    """

    if record_count <= 0:
        raise ValueError(
            "record_count must be greater than zero"
        )

    if order_item_count <= 0:
        raise ValueError(
            "order_item_count must be greater than zero"
        )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE retail.ingestion_batch_parts
            SET
                status = 'COMPLETED',
                record_count = %s,
                order_item_count = %s,
                completed_at = CURRENT_TIMESTAMP,
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE
                batch_id = %s
                AND part_number = %s
                AND status = 'STARTED'
            """,
            (
                record_count,
                order_item_count,
                batch_id,
                part_number,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Unable to complete ingestion "
                "batch part because it is not STARTED"
            )

def fail_batch_part(
    connection: Connection,
    *,
    batch_id: UUID,
    part_number: int,
    error_message: str,
) -> None:
    """
    Mark a physical batch part as FAILED.

    The failure checkpoint is committed independently
    so that it survives the surrounding ingestion failure.
    """

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                UPDATE retail.ingestion_batch_parts
                SET
                    status = 'FAILED',
                    error_message = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = %s
                  AND part_number = %s
                """,
            (
                error_message[:5000],
                batch_id,
                part_number,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Unable to fail ingestion "
                "batch part"
            )


def get_batch_part_start_ids(
    connection: Connection,
    *,
    batch_id: UUID,
) -> tuple[int, int] | None:
    """
    Return the original starting order_id and
    order_item_id for the logical batch.

    The first physical batch establishes the source
    ID allocation for the entire logical ingestion.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                start_order_id,
                start_order_item_id
            FROM retail.ingestion_batch_parts
            WHERE
                batch_id = %s
                AND part_number = 1
            """,
            (batch_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return (
        row[0],
        row[1],
    )

def get_completed_batch_parts(
    connection: Connection,
    *,
    batch_id: UUID,
) -> dict[int, dict[str, int]]:
    """
    Return completed physical parts and their
    persisted record counts.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                part_number,
                record_count,
                order_item_count
            FROM retail.ingestion_batch_parts
            WHERE batch_id = %s
              AND status = 'COMPLETED'
            ORDER BY part_number
            """,
            (batch_id,),
        )

        return {
            part_number: {
                "orders": record_count,
                "order_items": order_item_count,
            }
            for (
                part_number,
                record_count,
                order_item_count,
            ) in cursor.fetchall()
        }

def heartbeat_batch_part(
    connection: Connection,
    *,
    batch_id: UUID,
    part_number: int,
) -> None:
    """
    Update the timestamp of an active physical batch part.

    The physical part must still be STARTED.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE retail.ingestion_batch_parts
            SET
                updated_at = CURRENT_TIMESTAMP
            WHERE
                batch_id = %s
                AND part_number = %s
                AND status = 'STARTED'
            """,
            (
                batch_id,
                part_number,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Cannot heartbeat ingestion "
                "batch part because it is "
                "not STARTED"
            )
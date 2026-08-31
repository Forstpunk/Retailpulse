from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection


@dataclass(frozen=True)
class IngestionBatchState:
    batch_id: UUID
    source_system: str
    batch_type: str
    status: str
    record_count: int
    attempt_count: int
    started_at: datetime
    completed_at: datetime | None
    last_attempt_at: datetime
    error_message: str | None


def get_batch(
    connection: Connection,
    batch_id: UUID,
) -> IngestionBatchState | None:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                batch_id,
                source_system,
                batch_type,
                status,
                record_count,
                attempt_count,
                started_at,
                completed_at,
                last_attempt_at,
                error_message
            FROM retail.ingestion_batches
            WHERE batch_id = %s
            """,
            (batch_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return IngestionBatchState(
        batch_id=row[0],
        source_system=row[1],
        batch_type=row[2],
        status=row[3],
        record_count=row[4],
        attempt_count=row[5],
        started_at=row[6],
        completed_at=row[7],
        last_attempt_at=row[8],
        error_message=row[9],
    )


def start_batch(
    connection: Connection,
    batch_id: UUID,
    source_system: str,
    batch_type: str,
) -> bool:
    """
    Register a new logical ingestion batch.

    Returns True only when a new row is inserted.
    """

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                INSERT INTO retail.ingestion_batches (
                    batch_id,
                    source_system,
                    batch_type,
                    status,
                    attempt_count,
                    last_attempt_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'STARTED',
                    1,
                    CURRENT_TIMESTAMP
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


def retry_failed_batch(
    connection: Connection,
    batch_id: UUID,
    max_attempts: int | None = None,
) -> bool:
    """
    Move a FAILED logical ingestion batch back to STARTED.

    Parameters
    ----------
    connection:
        PostgreSQL connection.

    batch_id:
        Logical ingestion batch identifier.

    max_attempts:
        Optional retry limit.

        When provided, this value is used as the retry
        limit for this operation.

        When omitted, the batch's persisted max_attempts
        value is used.

    Returns
    -------
    bool
        True if the FAILED batch was successfully moved
        back to STARTED.

        False if the batch does not exist, is not FAILED,
        or has exhausted its retry limit.
    """

    with connection.transaction(), connection.cursor() as cursor:

        if max_attempts is None:

            cursor.execute(
                """
                    UPDATE retail.ingestion_batches
                    SET
                        status = 'STARTED',
                        attempt_count = attempt_count + 1,
                        last_attempt_at = CURRENT_TIMESTAMP,
                        last_heartbeat_at = CURRENT_TIMESTAMP,
                        completed_at = NULL,
                        error_message = NULL
                    WHERE
                        batch_id = %s
                        AND status = 'FAILED'
                        AND attempt_count < max_attempts
                    RETURNING attempt_count
                    """,
                (batch_id,),
            )

        else:

            if max_attempts <= 0:
                raise ValueError(
                    "max_attempts must be greater than zero"
                )

            cursor.execute(
                """
                    UPDATE retail.ingestion_batches
                    SET
                        status = 'STARTED',
                        attempt_count = attempt_count + 1,
                        last_attempt_at = CURRENT_TIMESTAMP,
                        last_heartbeat_at = CURRENT_TIMESTAMP,
                        completed_at = NULL,
                        error_message = NULL
                    WHERE
                        batch_id = %s
                        AND status = 'FAILED'
                        AND attempt_count < %s
                    RETURNING attempt_count
                    """,
                (
                    batch_id,
                    max_attempts,
                ),
            )

        row = cursor.fetchone()

    return row is not None


def complete_batch(
    connection: Connection,
    batch_id: UUID,
    record_count: int,
) -> None:

    if record_count < 0:
        raise ValueError(
            "record_count cannot be negative"
        )

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                UPDATE retail.ingestion_batches
                SET
                    status = 'COMPLETED',
                    record_count = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    last_heartbeat_at = CURRENT_TIMESTAMP,
                    error_message = NULL
                WHERE
                    batch_id = %s
                    AND status = 'STARTED'
                """,
            (
                record_count,
                batch_id,
            ),
        )

        if cursor.rowcount != 1:

            raise RuntimeError(
                f"Cannot complete batch "
                f"{batch_id}: "
                "batch is not STARTED"
            )


def fail_batch(
    connection: Connection,
    batch_id: UUID,
    error_message: str,
) -> None:

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                UPDATE retail.ingestion_batches
                SET
                    status = 'FAILED',
                    completed_at = CURRENT_TIMESTAMP,
                    last_heartbeat_at = CURRENT_TIMESTAMP,
                    error_message = %s
                WHERE
                    batch_id = %s
                    AND status = 'STARTED'
                """,
            (
                error_message[:5000],
                batch_id,
            ),
        )

        if cursor.rowcount != 1:

            raise RuntimeError(
                f"Cannot fail batch "
                f"{batch_id}: "
                "batch is not STARTED"
            )

def get_stale_started_batches(
    connection: Connection,
    *,
    stale_after_seconds: int,
) -> list[IngestionBatchState]:
    """
    Return logical ingestion batches that are still STARTED
    but have not sent a heartbeat within the configured
    threshold.

    This function is read-only.

    It does not change batch state.
    """

    if stale_after_seconds <= 0:
        raise ValueError(
            "stale_after_seconds must be greater than zero"
        )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                batch_id,
                source_system,
                batch_type,
                status,
                record_count,
                attempt_count,
                started_at,
                completed_at,
                last_attempt_at,
                error_message
            FROM retail.ingestion_batches
            WHERE
                status = 'STARTED'
                AND last_heartbeat_at <
                    CURRENT_TIMESTAMP
                    - (%s * INTERVAL '1 second')
            ORDER BY last_heartbeat_at
            """,
            (
                stale_after_seconds,
            ),
        )

        rows = cursor.fetchall()

    return [
        IngestionBatchState(
            batch_id=row[0],
            source_system=row[1],
            batch_type=row[2],
            status=row[3],
            record_count=row[4],
            attempt_count=row[5],
            started_at=row[6],
            completed_at=row[7],
            last_attempt_at=row[8],
            error_message=row[9],
        )
        for row in rows
    ]

def heartbeat_batch(
    connection: Connection,
    batch_id: UUID,
) -> None:
    """
    Update the heartbeat timestamp for a STARTED
    logical ingestion batch.

    The batch must still be STARTED.
    """

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                UPDATE retail.ingestion_batches
                SET
                    last_heartbeat_at = CURRENT_TIMESTAMP
                WHERE
                    batch_id = %s
                    AND status = 'STARTED'
                """,
            (
                batch_id,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Cannot heartbeat batch "
                f"{batch_id}: "
                "batch is not STARTED"
            )
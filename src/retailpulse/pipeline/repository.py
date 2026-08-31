from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection

from retailpulse.pipeline.errors import (
    DuplicateLogicalRunError,
)


@dataclass(frozen=True)
class ExistingPipelineRun:
    """
    Read-model of an existing analytics.pipeline_runs row,
    returned when a logical_run_id already has a run.
    """

    pipeline_run_id: UUID
    logical_run_id: str
    status: str
    batch_id: UUID | None
    ingestion_completed: bool
    quality_passed: bool
    analytics_completed: bool
    orders_loaded: int
    order_items_loaded: int
    analytics_rows: int
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


_EXISTING_RUN_COLUMNS = """
    pipeline_run_id,
    logical_run_id,
    status,
    batch_id,
    ingestion_completed,
    quality_passed,
    analytics_completed,
    orders_loaded,
    order_items_loaded,
    analytics_rows,
    started_at,
    completed_at,
    error_message
"""


def _row_to_existing_run(
    row: tuple,
) -> ExistingPipelineRun:

    return ExistingPipelineRun(
        pipeline_run_id=row[0],
        logical_run_id=row[1],
        status=row[2],
        batch_id=row[3],
        ingestion_completed=row[4],
        quality_passed=row[5],
        analytics_completed=row[6],
        orders_loaded=row[7],
        order_items_loaded=row[8],
        analytics_rows=row[9],
        started_at=row[10],
        completed_at=row[11],
        error_message=row[12],
    )


def get_pipeline_run(
    connection: Connection,
    *,
    logical_run_id: str,
) -> ExistingPipelineRun | None:
    """
    Look up the (at most one) pipeline run for a
    logical_run_id.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            SELECT {_EXISTING_RUN_COLUMNS}
            FROM analytics.pipeline_runs
            WHERE logical_run_id = %s
            """,
            (logical_run_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return _row_to_existing_run(row)


def start_pipeline_run(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
    logical_run_id: str,
    started_at: datetime,
) -> None:
    """
    Persist the beginning of a pipeline run.

    Race-safe idempotency: the INSERT relies on the
    unique index on logical_run_id as the actual
    safety boundary (ON CONFLICT DO NOTHING), not on an
    application-level check-then-insert. If a row for
    this logical_run_id already exists — whether it was
    committed a minute ago or by a concurrent request a
    millisecond ago — this raises DuplicateLogicalRunError
    describing the existing run's status instead of
    letting a raw UniqueViolation escape.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO analytics.pipeline_runs (
                pipeline_run_id,
                logical_run_id,
                status,
                started_at
            )
            VALUES (
                %s,
                %s,
                'RUNNING',
                %s
            )
            ON CONFLICT (logical_run_id) DO NOTHING
            RETURNING pipeline_run_id
            """,
            (
                pipeline_run_id,
                logical_run_id,
                started_at,
            ),
        )

        inserted = cursor.fetchone()

    if inserted is not None:
        return

    existing = get_pipeline_run(
        connection,
        logical_run_id=logical_run_id,
    )

    if existing is None:
        # Extremely unlikely: the conflicting row was
        # deleted between the INSERT and our lookup.
        raise DuplicateLogicalRunError(
            logical_run_id=logical_run_id,
            existing_pipeline_run_id="unknown",
            existing_status="unknown",
        )

    raise DuplicateLogicalRunError(
        logical_run_id=logical_run_id,
        existing_pipeline_run_id=str(
            existing.pipeline_run_id
        ),
        existing_status=existing.status,
    )


def reopen_failed_pipeline_run(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
) -> bool:
    """
    Transition a FAILED pipeline run back to RUNNING so
    it can be resumed, without minting a new
    pipeline_run_id (logical_run_id stays unique).

    The UPDATE ... WHERE status = 'FAILED' guard makes
    this race-safe: if two callers try to resume the
    same run concurrently, only one UPDATE affects a row.

    Returns True if this call reopened the run, False if
    it was not in FAILED status (e.g. already reopened by
    a concurrent caller, or already SUCCESS/RUNNING).
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_runs
            SET
                status = 'RUNNING',
                completed_at = NULL,
                duration_seconds = NULL,
                error_message = NULL
            WHERE pipeline_run_id = %s
              AND status = 'FAILED'
            """,
            (pipeline_run_id,),
        )

        return cursor.rowcount == 1


def complete_pipeline_run(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
    batch_id: UUID,
    orders_loaded: int,
    order_items_loaded: int,
    analytics_rows: int,
    started_at: datetime,
    completed_at: datetime,
) -> None:
    """
    Mark a pipeline run as successfully completed.
    """

    duration_seconds = (
        completed_at - started_at
    ).total_seconds()

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_runs
            SET
                batch_id = %s,

                status = 'SUCCESS',

                ingestion_completed = TRUE,

                quality_passed = TRUE,

                analytics_completed = TRUE,

                orders_loaded = %s,

                order_items_loaded = %s,

                analytics_rows = %s,

                completed_at = %s,

                duration_seconds = %s

            WHERE pipeline_run_id = %s
            """,
            (
                batch_id,
                orders_loaded,
                order_items_loaded,
                analytics_rows,
                completed_at,
                duration_seconds,
                pipeline_run_id,
            ),
        )


def fail_pipeline_run(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
    batch_id: UUID | None,
    ingestion_completed: bool,
    quality_passed: bool,
    analytics_completed: bool,
    orders_loaded: int,
    order_items_loaded: int,
    analytics_rows: int,
    started_at: datetime,
    completed_at: datetime,
    error_message: str,
) -> None:
    """
    Mark a pipeline run as failed.
    """

    duration_seconds = (
        completed_at - started_at
    ).total_seconds()

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_runs
            SET
                batch_id = %s,

                status = 'FAILED',

                ingestion_completed = %s,

                quality_passed = %s,

                analytics_completed = %s,

                orders_loaded = %s,

                order_items_loaded = %s,

                analytics_rows = %s,

                completed_at = %s,

                duration_seconds = %s,

                error_message = %s

            WHERE pipeline_run_id = %s
            """,
            (
                batch_id,
                ingestion_completed,
                quality_passed,
                analytics_completed,
                orders_loaded,
                order_items_loaded,
                analytics_rows,
                completed_at,
                duration_seconds,
                error_message,
                pipeline_run_id,
            ),
        )
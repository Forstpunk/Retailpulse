from datetime import datetime
from uuid import UUID

from psycopg import Connection


def start_stage_run(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
    stage_name: str,
    attempt: int = 1,
    started_at: datetime,
) -> int:
    """
    Persist the beginning of a pipeline stage execution.

    Returns:
        The generated stage_run_id.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO analytics.pipeline_stage_runs (
                pipeline_run_id,
                stage_name,
                status,
                attempt,
                started_at
            )
            VALUES (
                %s,
                %s,
                'RUNNING',
                %s,
                %s
            )
            RETURNING stage_run_id
            """,
            (
                pipeline_run_id,
                stage_name,
                attempt,
                started_at,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "Failed to create pipeline stage run."
        )

    return int(row[0])


def complete_stage_run(
    connection: Connection,
    *,
    stage_run_id: int,
    completed_at: datetime,
    duration_ms: int,
    records_processed: int | None = None,
) -> None:
    """
    Mark a pipeline stage as successfully completed.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_stage_runs
            SET
                status = 'SUCCESS',
                completed_at = %s,
                duration_ms = %s,
                records_processed = %s
            WHERE stage_run_id = %s
            """,
            (
                completed_at,
                duration_ms,
                records_processed,
                stage_run_id,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Pipeline stage run was not found: "
                f"{stage_run_id}"
            )


def fail_stage_run(
    connection: Connection,
    *,
    stage_run_id: int,
    completed_at: datetime,
    duration_ms: int,
    error_category: str | None,
    error_message: str,
    records_processed: int | None = None,
) -> None:
    """
    Mark a pipeline stage as failed.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_stage_runs
            SET
                status = 'FAILED',
                completed_at = %s,
                duration_ms = %s,
                records_processed = %s,
                error_category = %s,
                error_message = %s
            WHERE stage_run_id = %s
            """,
            (
                completed_at,
                duration_ms,
                records_processed,
                error_category,
                error_message,
                stage_run_id,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Pipeline stage run was not found: "
                f"{stage_run_id}"
            )

def update_stage_records_processed(
    connection: Connection,
    *,
    stage_run_id: int,
    records_processed: int,
) -> None:
    """
    Update the number of records processed by a stage attempt.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            UPDATE analytics.pipeline_stage_runs
            SET
                records_processed = %s
            WHERE stage_run_id = %s
            """,
            (
                records_processed,
                stage_run_id,
            ),
        )

    connection.commit()
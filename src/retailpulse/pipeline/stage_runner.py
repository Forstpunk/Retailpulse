from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import TypeVar
from uuid import UUID

from psycopg import Connection

from retailpulse.pipeline.errors import (
    classify_pipeline_error,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
    run_with_retry,
)
from retailpulse.pipeline.stage_repository import (
    complete_stage_run,
    fail_stage_run,
    start_stage_run,
    update_stage_records_processed,
)

T = TypeVar("T")


def run_stage_with_retry(
    connection: Connection,
    *,
    pipeline_run_id: UUID,
    stage_name: str,
    operation: Callable[[], T],
    retry_config: RetryConfig,
    records_processed: Callable[
        [T],
        int | None,
    ]
    | None = None,
) -> T:
    """
    Execute a pipeline stage with retry support.

    Every retry attempt is persisted separately.
    """

    current_attempt = 0

    active_stage_run_id: int | None = None

    active_started_perf: float | None = None

    successful_stage_run_id: int | None = None

    def execute_attempt() -> T:

        nonlocal current_attempt
        nonlocal active_stage_run_id
        nonlocal active_started_perf

        current_attempt += 1

        started_at = datetime.now(
            UTC
        )

        active_started_perf = perf_counter()

        active_stage_run_id = (
            start_stage_run(
                connection,
                pipeline_run_id=(
                    pipeline_run_id
                ),
                stage_name=stage_name,
                attempt=current_attempt,
                started_at=started_at,
            )
        )

        return operation()

    def handle_attempt(
        attempt: int,
        exception: Exception | None,
    ) -> None:

        nonlocal active_stage_run_id
        nonlocal active_started_perf
        nonlocal successful_stage_run_id

        if active_stage_run_id is None:

            raise RuntimeError(
                "Stage attempt callback received "
                "without an active stage run."
            )

        if active_started_perf is None:

            raise RuntimeError(
                "Stage attempt callback received "
                "without a start timestamp."
            )

        duration_ms = int(
            (
                perf_counter()
                - active_started_perf
            )
            * 1000
        )

        completed_at = datetime.now(
            UTC
        )

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        if exception is None:

            complete_stage_run(
                connection,
                stage_run_id=(
                    active_stage_run_id
                ),
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

            successful_stage_run_id = (
                active_stage_run_id
            )

        # -----------------------------------------------------
        # FAILURE
        # -----------------------------------------------------

        else:

            error_category = (
                classify_pipeline_error(
                    exception
                )
            )

            fail_stage_run(
                connection,
                stage_run_id=(
                    active_stage_run_id
                ),
                completed_at=completed_at,
                duration_ms=duration_ms,
                error_category=(
                    error_category.value
                ),
                error_message=str(
                    exception
                ),
            )

        active_stage_run_id = None

        active_started_perf = None

    result = run_with_retry(
        execute_attempt,
        operation_name=stage_name,
        retry_config=retry_config,
        on_attempt=handle_attempt,
    )

    # ---------------------------------------------------------
    # Update successful attempt's record count.
    # ---------------------------------------------------------

    if (
        records_processed is not None
        and successful_stage_run_id is not None
    ):

        processed = records_processed(
            result
        )

        if processed is not None:

            update_stage_records_processed(
                connection,
                stage_run_id=(
                    successful_stage_run_id
                ),
                records_processed=processed,
            )

    return result
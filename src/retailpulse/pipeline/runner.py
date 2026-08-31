from datetime import UTC, datetime
from uuid import UUID, uuid4

from psycopg import Connection

from retailpulse.analytics.build import (
    build_analytics,
)
from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.bootstrap import (
    reference_data_is_ready,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.generators.reference_loader import (
    bootstrap_reference_data,
)
from retailpulse.generators.transaction_ingestion import (
    run_transaction_ingestion,
)
from retailpulse.observability.logging import (
    get_logger,
)
from retailpulse.pipeline.errors import (
    DuplicateLogicalRunError,
    classify_pipeline_error,
)
from retailpulse.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)
from retailpulse.pipeline.repository import (
    complete_pipeline_run,
    fail_pipeline_run,
    get_pipeline_run,
    reopen_failed_pipeline_run,
    start_pipeline_run,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
)
from retailpulse.pipeline.stage_runner import (
    run_stage_with_retry,
)

logger = get_logger(
    __name__
)


# =============================================================
# Retry configuration
# =============================================================

DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay_seconds=1.0,
    enabled=True,
)


# =============================================================
# Pipeline runner
# =============================================================

def run_pipeline(
    connection: Connection,
    config: GeneratorConfig,
    *,
    logical_run_id: str | None = None,
) -> PipelineResult:
    """
    Execute the complete RetailPulse pipeline for a new
    logical run.

    Pipeline flow:

        Transaction ingestion
                ↓
        Reconciliation + quality
                ↓
        Analytics build
                ↓
        Pipeline completion

    Idempotency:

        Each logical_run_id may have exactly one
        pipeline_runs row, enforced by a unique index
        (see start_pipeline_run). If a row already exists
        for this logical_run_id, the pipeline is NOT
        executed again; a SKIPPED PipelineResult describing
        the existing run is returned instead. A FAILED
        logical run must be explicitly retried via
        resume_pipeline() rather than by calling
        run_pipeline() again with the same id.
    """

    pipeline_run_id = uuid4()

    if logical_run_id is None:

        logical_run_id = (
            f"pipeline-{uuid4()}"
        )

    started_at = datetime.now(
        UTC
    )

    logger.info(
        "Pipeline started "
        "pipeline_run_id=%s "
        "logical_run_id=%s",
        pipeline_run_id,
        logical_run_id,
    )

    try:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=logical_run_id,
            started_at=started_at,
        )

    except DuplicateLogicalRunError as exc:

        logger.warning(
            "Pipeline run skipped: logical_run_id=%s "
            "already has pipeline_run_id=%s "
            "status=%s",
            logical_run_id,
            exc.existing_pipeline_run_id,
            exc.existing_status,
        )

        return _skipped_result(exc)

    logger.info(
        "Pipeline run persisted as RUNNING "
        "pipeline_run_id=%s",
        pipeline_run_id,
    )

    return _execute_pipeline_stages(
        connection,
        config,
        pipeline_run_id=pipeline_run_id,
        logical_run_id=logical_run_id,
        started_at=started_at,
    )


def resume_pipeline(
    connection: Connection,
    config: GeneratorConfig,
    *,
    logical_run_id: str,
) -> PipelineResult:
    """
    Resume a previously FAILED logical run.

    Reuses the existing pipeline_run_id (a logical run
    only ever owns one pipeline_runs row) and skips stages
    that already completed successfully before the
    failure — e.g. if transaction_ingestion succeeded but
    analytics_build failed, resuming re-runs only
    analytics_build.

    Raises ValueError if there is no run for
    logical_run_id, or if the run is not currently FAILED
    (already SUCCESS, or still RUNNING and therefore
    unsafe to resume concurrently).
    """

    existing = get_pipeline_run(
        connection,
        logical_run_id=logical_run_id,
    )

    if existing is None:
        raise ValueError(
            "No pipeline run found for "
            f"logical_run_id={logical_run_id!r}; "
            "nothing to resume."
        )

    if existing.status == "SUCCESS":
        raise ValueError(
            f"logical_run_id={logical_run_id!r} already "
            "completed successfully; resume is a no-op. "
            "Use a new logical_run_id to run again."
        )

    if existing.status == "RUNNING":
        raise ValueError(
            f"logical_run_id={logical_run_id!r} is "
            "currently RUNNING "
            f"(pipeline_run_id={existing.pipeline_run_id}); "
            "refusing to resume a run that may still be "
            "in-flight."
        )

    reopened = reopen_failed_pipeline_run(
        connection,
        pipeline_run_id=existing.pipeline_run_id,
    )

    if not reopened:
        raise ValueError(
            f"logical_run_id={logical_run_id!r} was no "
            "longer FAILED when attempting to resume "
            "(concurrent change); refusing to proceed."
        )

    logger.info(
        "Pipeline resumed "
        "pipeline_run_id=%s "
        "logical_run_id=%s "
        "skip_ingestion=%s",
        existing.pipeline_run_id,
        logical_run_id,
        existing.ingestion_completed,
    )

    return _execute_pipeline_stages(
        connection,
        config,
        pipeline_run_id=existing.pipeline_run_id,
        logical_run_id=logical_run_id,
        started_at=existing.started_at,
        skip_ingestion=existing.ingestion_completed,
        batch_id=(
            str(existing.batch_id)
            if existing.batch_id is not None
            else None
        ),
        orders_loaded=existing.orders_loaded,
        order_items_loaded=existing.order_items_loaded,
    )


def _skipped_result(
    exc: DuplicateLogicalRunError,
) -> PipelineResult:
    """
    Build the PipelineResult for a logical run that was
    not executed because a pipeline run already exists.
    """

    return PipelineResult(
        status=PipelineStatus.SKIPPED,
        pipeline_run_id=(
            exc.existing_pipeline_run_id
        ),
        logical_run_id=exc.logical_run_id,
        ingestion_completed=False,
        quality_passed=False,
        analytics_completed=False,
        batch_id=None,
        orders_loaded=0,
        order_items_loaded=0,
        analytics_rows=0,
        error_category=None,
        message=(
            f"Logical run '{exc.logical_run_id}' already "
            f"has a pipeline run with status "
            f"{exc.existing_status} "
            f"(pipeline_run_id="
            f"{exc.existing_pipeline_run_id}). "
            + (
                "Resume with resume_pipeline() to retry."
                if exc.existing_status == "FAILED"
                else "No action taken."
            )
        ),
    )


def _ensure_reference_data_and_ingest(
    connection: Connection,
    config: GeneratorConfig,
    *,
    logical_run_id: str,
    pipeline_run_id: UUID,
) -> dict[str, int | str | float]:
    """
    Bootstrap source-system reference data (categories,
    suppliers, stores, products, customers) on a fresh
    environment before generating transactions against it.

    reference_data_is_ready() is a cheap idempotency check,
    so this is safe to call on every transaction_ingestion
    attempt — after the first successful run it is a no-op.
    """

    if not reference_data_is_ready(
        connection,
        config,
    ):

        logger.info(
            "Reference data not yet initialized; "
            "bootstrapping pipeline_run_id=%s",
            pipeline_run_id,
        )

        bootstrap_reference_data(
            connection,
            config,
        )

    return run_transaction_ingestion(
        connection,
        config,
        logical_run_id=logical_run_id,
        pipeline_run_id=pipeline_run_id,
    )


def _execute_pipeline_stages(
    connection: Connection,
    config: GeneratorConfig,
    *,
    pipeline_run_id: UUID,
    logical_run_id: str,
    started_at: datetime,
    skip_ingestion: bool = False,
    batch_id: str | None = None,
    orders_loaded: int = 0,
    order_items_loaded: int = 0,
) -> PipelineResult:
    """
    Run the stages of a pipeline execution against an
    already-persisted RUNNING pipeline_runs row, and
    persist the final SUCCESS/FAILED outcome.

    Shared by run_pipeline() (fresh runs) and
    resume_pipeline() (continuing a FAILED run), which
    differ only in whether transaction_ingestion needs to
    run at all.
    """

    analytics_rows = 0

    ingestion_completed = skip_ingestion
    quality_passed = skip_ingestion
    analytics_completed = False

    # =========================================================
    # Step 1: Transaction ingestion
    # =========================================================

    if not skip_ingestion:

        try:

            logger.info(
                "Transaction ingestion started "
                "pipeline_run_id=%s",
                pipeline_run_id,
            )

            ingestion_result = (
                run_stage_with_retry(
                    connection,
                    pipeline_run_id=pipeline_run_id,
                    stage_name="transaction_ingestion",
                    operation=lambda: (
                        _ensure_reference_data_and_ingest(
                            connection,
                            config,
                            logical_run_id=logical_run_id,
                            pipeline_run_id=pipeline_run_id,
                        )
                    ),
                    retry_config=DEFAULT_RETRY_CONFIG,
                    records_processed=(
                        lambda result: (
                            int(result["orders"])
                            + int(result["order_items"])
                        )
                    ),
                )
            )

            batch_id = str(
                ingestion_result["batch_id"]
            )

            orders_loaded = int(
                ingestion_result["orders"]
            )

            order_items_loaded = int(
                ingestion_result["order_items"]
            )

            ingestion_completed = True

            # Transaction ingestion owns the quality gate:
            # if reconciliation or quality fails,
            # run_transaction_ingestion() raises.
            quality_passed = True

            logger.info(
                "Transaction ingestion completed "
                "pipeline_run_id=%s "
                "batch_id=%s "
                "orders=%s "
                "order_items=%s",
                pipeline_run_id,
                batch_id,
                orders_loaded,
                order_items_loaded,
            )

        except Exception as exc:

            return _fail_and_build_result(
                connection,
                exc,
                stage_name="transaction_ingestion",
                pipeline_run_id=pipeline_run_id,
                logical_run_id=logical_run_id,
                started_at=started_at,
                batch_id=batch_id,
                ingestion_completed=ingestion_completed,
                quality_passed=quality_passed,
                analytics_completed=analytics_completed,
                orders_loaded=orders_loaded,
                order_items_loaded=order_items_loaded,
                analytics_rows=analytics_rows,
            )

    else:

        logger.info(
            "Transaction ingestion skipped on resume "
            "pipeline_run_id=%s batch_id=%s",
            pipeline_run_id,
            batch_id,
        )

    # =========================================================
    # Step 2: Analytics build
    # =========================================================

    try:

        logger.info(
            "Analytics build started "
            "pipeline_run_id=%s "
            "batch_id=%s",
            pipeline_run_id,
            batch_id,
        )

        analytics_result = (
            run_stage_with_retry(
                connection,
                pipeline_run_id=pipeline_run_id,
                stage_name="analytics_build",
                operation=lambda: (
                    build_analytics(connection)
                ),
                retry_config=DEFAULT_RETRY_CONFIG,
                records_processed=(
                    lambda result: int(
                        result.total_rows
                    )
                ),
            )
        )

        analytics_rows = int(
            analytics_result.total_rows
        )

        analytics_completed = True

        logger.info(
            "Analytics build completed "
            "pipeline_run_id=%s "
            "batch_id=%s "
            "rows=%s",
            pipeline_run_id,
            batch_id,
            analytics_rows,
        )

    except Exception as exc:

        return _fail_and_build_result(
            connection,
            exc,
            stage_name="analytics_build",
            pipeline_run_id=pipeline_run_id,
            logical_run_id=logical_run_id,
            started_at=started_at,
            batch_id=batch_id,
            ingestion_completed=ingestion_completed,
            quality_passed=quality_passed,
            analytics_completed=analytics_completed,
            orders_loaded=orders_loaded,
            order_items_loaded=order_items_loaded,
            analytics_rows=analytics_rows,
        )

    # =========================================================
    # Step 3: Persist successful pipeline completion
    # =========================================================

    completed_at = datetime.now(UTC)

    complete_pipeline_run(
        connection,
        pipeline_run_id=pipeline_run_id,
        batch_id=UUID(batch_id),
        orders_loaded=orders_loaded,
        order_items_loaded=order_items_loaded,
        analytics_rows=analytics_rows,
        started_at=started_at,
        completed_at=completed_at,
    )

    logger.info(
        "Pipeline run persisted as SUCCESS "
        "pipeline_run_id=%s "
        "logical_run_id=%s "
        "batch_id=%s",
        pipeline_run_id,
        logical_run_id,
        batch_id,
    )

    return PipelineResult(
        status=PipelineStatus.SUCCESS,
        pipeline_run_id=str(pipeline_run_id),
        logical_run_id=logical_run_id,
        ingestion_completed=True,
        quality_passed=True,
        analytics_completed=True,
        batch_id=batch_id,
        orders_loaded=orders_loaded,
        order_items_loaded=order_items_loaded,
        analytics_rows=analytics_rows,
        error_category=None,
        message=(
            "RetailPulse pipeline completed successfully."
        ),
    )


def _fail_and_build_result(
    connection: Connection,
    exc: Exception,
    *,
    stage_name: str,
    pipeline_run_id: UUID,
    logical_run_id: str,
    started_at: datetime,
    batch_id: str | None,
    ingestion_completed: bool,
    quality_passed: bool,
    analytics_completed: bool,
    orders_loaded: int,
    order_items_loaded: int,
    analytics_rows: int,
) -> PipelineResult:
    """
    Classify a stage failure, persist the pipeline as
    FAILED, and build the FAILED PipelineResult. Shared by
    both stage try/except blocks in
    _execute_pipeline_stages().
    """

    error_category = classify_pipeline_error(exc)

    logger.exception(
        "%s failed pipeline_run_id=%s batch_id=%s "
        "error_category=%s",
        stage_name,
        pipeline_run_id,
        batch_id,
        error_category,
    )

    completed_at = datetime.now(UTC)

    fail_pipeline_run(
        connection,
        pipeline_run_id=pipeline_run_id,
        batch_id=(
            UUID(batch_id)
            if batch_id is not None
            else None
        ),
        ingestion_completed=ingestion_completed,
        quality_passed=quality_passed,
        analytics_completed=analytics_completed,
        orders_loaded=orders_loaded,
        order_items_loaded=order_items_loaded,
        analytics_rows=analytics_rows,
        started_at=started_at,
        completed_at=completed_at,
        error_message=(
            f"[{error_category.value}] "
            f"{stage_name} failed: {exc}"
        ),
    )

    logger.error(
        "Pipeline marked FAILED pipeline_run_id=%s "
        "stage=%s error_category=%s",
        pipeline_run_id,
        stage_name,
        error_category,
    )

    return PipelineResult(
        status=PipelineStatus.FAILED,
        pipeline_run_id=str(pipeline_run_id),
        logical_run_id=logical_run_id,
        ingestion_completed=ingestion_completed,
        quality_passed=quality_passed,
        analytics_completed=analytics_completed,
        batch_id=batch_id,
        orders_loaded=orders_loaded,
        order_items_loaded=order_items_loaded,
        analytics_rows=analytics_rows,
        error_category=error_category,
        message=f"{stage_name} failed: {exc}",
    )


# =============================================================
# CLI entry point
# =============================================================

if __name__ == "__main__":

    config = GeneratorConfig()

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            config,
        )

    print()
    print(
        "========================================"
    )
    print(
        "       RetailPulse Pipeline Result"
    )
    print(
        "========================================"
    )

    print(
        f"Status: {result.status}"
    )

    print(
        f"Pipeline Run ID: "
        f"{result.pipeline_run_id}"
    )

    print(
        f"Logical Run ID: "
        f"{result.logical_run_id}"
    )

    print(
        f"Batch ID: "
        f"{result.batch_id}"
    )

    print(
        f"Orders loaded: "
        f"{result.orders_loaded:,}"
    )

    print(
        f"Order items loaded: "
        f"{result.order_items_loaded:,}"
    )

    print(
        f"Analytics rows: "
        f"{result.analytics_rows:,}"
    )

    print(
        f"Ingestion completed: "
        f"{result.ingestion_completed}"
    )

    print(
        f"Quality passed: "
        f"{result.quality_passed}"
    )

    print(
        f"Analytics completed: "
        f"{result.analytics_completed}"
    )

    print(
        f"Error category: "
        f"{result.error_category}"
    )

    print(
        f"Message: "
        f"{result.message}"
    )

    print(
        "========================================"
    )

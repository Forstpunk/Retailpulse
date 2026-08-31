from datetime import UTC, datetime
from uuid import uuid4

import pytest

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.pipeline.errors import (
    DuplicateLogicalRunError,
)
from retailpulse.pipeline.models import (
    PipelineStatus,
)
from retailpulse.pipeline.repository import (
    fail_pipeline_run,
    start_pipeline_run,
)
from retailpulse.pipeline.runner import (
    run_pipeline,
)


def _small_config() -> GeneratorConfig:

    return GeneratorConfig(
        seed=4242,
        categories=10,
        suppliers=10,
        stores=5,
        products=50,
        customers=100,
        orders=12,
        order_items=30,
        payments=12,
        returns=3,
        batch_size=10,
    )


def test_first_logical_run_succeeds() -> None:

    logical_run_id = (
        f"idempotency-first-{uuid4()}"
    )

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        result.status
        == PipelineStatus.SUCCESS
    )

    assert (
        result.logical_run_id
        == logical_run_id
    )


def test_duplicate_success_logical_run_is_skipped() -> None:

    logical_run_id = (
        f"idempotency-success-{uuid4()}"
    )

    with get_connection() as connection:

        first = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        first.status
        == PipelineStatus.SUCCESS
    )

    with get_connection() as connection:

        second = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        second.status
        == PipelineStatus.SKIPPED
    )

    # The skipped result must describe the ORIGINAL run,
    # not a new pipeline_run_id that was never persisted.
    assert (
        second.pipeline_run_id
        == first.pipeline_run_id
    )

    assert "SUCCESS" in second.message


def test_duplicate_running_logical_run_is_skipped() -> None:

    logical_run_id = (
        f"idempotency-running-{uuid4()}"
    )

    running_pipeline_run_id = uuid4()

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=(
                running_pipeline_run_id
            ),
            logical_run_id=logical_run_id,
            started_at=datetime.now(
                UTC
            ),
        )

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        result.status
        == PipelineStatus.SKIPPED
    )

    assert (
        result.pipeline_run_id
        == str(running_pipeline_run_id)
    )

    assert "RUNNING" in result.message


def test_duplicate_failed_logical_run_is_skipped_and_points_to_resume() -> None:

    logical_run_id = (
        f"idempotency-failed-{uuid4()}"
    )

    failed_pipeline_run_id = uuid4()

    started_at = datetime.now(
        UTC
    )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=(
                failed_pipeline_run_id
            ),
            logical_run_id=logical_run_id,
            started_at=started_at,
        )

        fail_pipeline_run(
            connection,
            pipeline_run_id=(
                failed_pipeline_run_id
            ),
            batch_id=None,
            ingestion_completed=False,
            quality_passed=False,
            analytics_completed=False,
            orders_loaded=0,
            order_items_loaded=0,
            analytics_rows=0,
            started_at=started_at,
            completed_at=datetime.now(
                UTC
            ),
            error_message="simulated failure",
        )

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        result.status
        == PipelineStatus.SKIPPED
    )

    assert (
        result.pipeline_run_id
        == str(failed_pipeline_run_id)
    )

    assert "resume_pipeline" in result.message


def test_start_pipeline_run_is_race_safe_at_the_database_boundary() -> None:
    """
    The application never performs a check-then-insert:
    start_pipeline_run() always attempts the INSERT and
    lets the unique index be the single source of truth,
    which is what makes duplicate detection safe under
    concurrent callers. This test proves the DB boundary
    itself rejects a second insert for the same
    logical_run_id, rather than relying on any
    application-level pre-check.
    """

    logical_run_id = (
        f"idempotency-race-{uuid4()}"
    )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=uuid4(),
            logical_run_id=logical_run_id,
            started_at=datetime.now(
                UTC
            ),
        )

        with pytest.raises(
            DuplicateLogicalRunError
        ) as exc_info:

            start_pipeline_run(
                connection,
                pipeline_run_id=uuid4(),
                logical_run_id=logical_run_id,
                started_at=datetime.now(
                    UTC
                ),
            )

    assert (
        exc_info.value.existing_status
        == "RUNNING"
    )

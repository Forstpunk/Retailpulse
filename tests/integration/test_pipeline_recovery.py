from datetime import UTC, datetime
from uuid import uuid4

import pytest

import retailpulse.pipeline.runner as runner_module
from retailpulse.analytics.build import (
    build_analytics as real_build_analytics,
)
from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.pipeline.errors import (
    TransientPipelineError,
)
from retailpulse.pipeline.models import (
    PipelineStatus,
)
from retailpulse.pipeline.repository import (
    start_pipeline_run,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
)
from retailpulse.pipeline.runner import (
    resume_pipeline,
    run_pipeline,
)


def _small_config() -> GeneratorConfig:

    return GeneratorConfig(
        seed=9191,
        categories=10,
        suppliers=10,
        stores=5,
        products=50,
        customers=100,
        orders=15,
        order_items=40,
        payments=15,
        returns=3,
        batch_size=10,
    )


def test_resume_pipeline_raises_if_no_run_found() -> None:

    with get_connection() as connection, pytest.raises(ValueError):

        resume_pipeline(
            connection,
            _small_config(),
            logical_run_id=(
                f"recovery-missing-{uuid4()}"
            ),
        )


def test_resume_pipeline_raises_if_already_success() -> None:

    logical_run_id = (
        f"recovery-success-{uuid4()}"
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

    with get_connection() as connection, pytest.raises(ValueError):

        resume_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )


def test_resume_pipeline_raises_if_still_running() -> None:

    logical_run_id = (
        f"recovery-running-{uuid4()}"
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

    with get_connection() as connection, pytest.raises(ValueError):

        resume_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )


def test_resume_pipeline_reruns_only_the_failed_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    transaction_ingestion succeeds, analytics_build fails.
    Resuming must NOT regenerate transactions (ingestion
    stays SKIPPED-on-resume) and must reuse the same
    pipeline_run_id and batch_id.
    """

    logical_run_id = (
        f"recovery-resume-{uuid4()}"
    )

    state = {"should_fail": True}

    def flaky_build_analytics(connection):

        if state["should_fail"]:

            raise TransientPipelineError(
                "simulated analytics failure"
            )

        return real_build_analytics(
            connection
        )

    monkeypatch.setattr(
        runner_module,
        "build_analytics",
        flaky_build_analytics,
    )

    # Fast retries: this test intentionally exhausts the
    # analytics_build retry budget once.
    monkeypatch.setattr(
        runner_module,
        "DEFAULT_RETRY_CONFIG",
        RetryConfig(
            max_attempts=2,
            base_delay_seconds=0,
        ),
    )

    with get_connection() as connection:

        first_result = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        first_result.status
        == PipelineStatus.FAILED
    )

    assert first_result.ingestion_completed

    assert not first_result.analytics_completed

    assert first_result.orders_loaded == 15

    state["should_fail"] = False

    with get_connection() as connection:

        resumed_result = resume_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        resumed_result.status
        == PipelineStatus.SUCCESS
    )

    assert (
        resumed_result.pipeline_run_id
        == first_result.pipeline_run_id
    )

    assert resumed_result.ingestion_completed

    assert resumed_result.analytics_completed

    assert (
        resumed_result.orders_loaded == 15
    )

    assert (
        resumed_result.batch_id
        == first_result.batch_id
    )

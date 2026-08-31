from datetime import UTC, datetime
from uuid import uuid4

import pytest

import retailpulse.pipeline.runner as runner_module
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
    run_pipeline,
)
from retailpulse.pipeline.stage_runner import (
    run_stage_with_retry,
)


def _small_config() -> GeneratorConfig:

    return GeneratorConfig(
        seed=5151,
        categories=10,
        suppliers=10,
        stores=5,
        products=50,
        customers=100,
        orders=10,
        order_items=25,
        payments=10,
        returns=2,
        batch_size=10,
    )


def test_v_latest_pipeline_runs_includes_recent_run() -> None:

    logical_run_id = (
        f"views-latest-{uuid4()}"
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

    with get_connection() as connection, connection.cursor() as cursor:

        cursor.execute(
            """
                SELECT status, age_seconds
                FROM analytics.v_latest_pipeline_runs
                WHERE pipeline_run_id = %s
                """,
            (result.pipeline_run_id,),
        )

        row = cursor.fetchone()

    assert row is not None

    assert row[0] == "SUCCESS"

    assert row[1] >= 0


def test_v_pipeline_stage_summary_reports_retry_then_success() -> None:

    pipeline_run_id = uuid4()

    calls = 0

    def operation() -> str:

        nonlocal calls

        calls += 1

        if calls == 1:

            raise TransientPipelineError(
                "temporary failure"
            )

        return "success"

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=(
                f"views-stage-summary-{uuid4()}"
            ),
            started_at=datetime.now(
                UTC
            ),
        )

        run_stage_with_retry(
            connection,
            pipeline_run_id=pipeline_run_id,
            stage_name="analytics_build",
            operation=operation,
            retry_config=RetryConfig(
                max_attempts=2,
                base_delay_seconds=0,
            ),
            records_processed=lambda _: 42,
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    attempt_count,
                    successful_attempt,
                    final_status,
                    records_processed,
                    total_duration_ms
                FROM analytics.v_pipeline_stage_summary
                WHERE pipeline_run_id = %s
                  AND stage_name = 'analytics_build'
                """,
                (pipeline_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == 2

    assert row[1] == 2

    assert row[2] == "SUCCESS"

    assert row[3] == 42

    assert row[4] is not None


def test_v_pipeline_failures_lists_failed_attempts() -> None:

    pipeline_run_id = uuid4()

    def always_fails() -> None:

        raise TransientPipelineError(
            "permanent-for-this-test failure"
        )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=(
                f"views-failures-{uuid4()}"
            ),
            started_at=datetime.now(
                UTC
            ),
        )

        with pytest.raises(
            TransientPipelineError
        ):

            run_stage_with_retry(
                connection,
                pipeline_run_id=pipeline_run_id,
                stage_name="transaction_ingestion",
                operation=always_fails,
                retry_config=RetryConfig(
                    max_attempts=1,
                    base_delay_seconds=0,
                ),
            )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    logical_run_id,
                    stage_name,
                    attempt,
                    error_category,
                    error_message
                FROM analytics.v_pipeline_failures
                WHERE pipeline_run_id = %s
                """,
                (pipeline_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[1] == "transaction_ingestion"

    assert row[2] == 1

    assert row[3] == "TRANSIENT"

    assert (
        "permanent-for-this-test failure"
        in row[4]
    )


def test_v_pipeline_health_reports_failed_stage_for_failed_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def always_fails_analytics(connection):

        raise TransientPipelineError(
            "simulated analytics failure"
        )

    monkeypatch.setattr(
        runner_module,
        "build_analytics",
        always_fails_analytics,
    )

    monkeypatch.setattr(
        runner_module,
        "DEFAULT_RETRY_CONFIG",
        RetryConfig(
            max_attempts=2,
            base_delay_seconds=0,
        ),
    )

    logical_run_id = (
        f"views-health-{uuid4()}"
    )

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            _small_config(),
            logical_run_id=logical_run_id,
        )

    assert (
        result.status
        == PipelineStatus.FAILED
    )

    with get_connection() as connection, connection.cursor() as cursor:

        cursor.execute(
            """
                SELECT
                    status,
                    failed_stage,
                    retry_count,
                    error_category
                FROM analytics.v_pipeline_health
                WHERE pipeline_run_id = %s
                """,
            (result.pipeline_run_id,),
        )

        row = cursor.fetchone()

    assert row is not None

    assert row[0] == "FAILED"

    assert row[1] == "analytics_build"

    assert row[2] >= 1

    assert row[3] == "TRANSIENT"

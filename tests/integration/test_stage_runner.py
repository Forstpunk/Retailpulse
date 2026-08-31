from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.pipeline.errors import (
    TransientPipelineError,
)
from retailpulse.pipeline.repository import (
    start_pipeline_run,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
)
from retailpulse.pipeline.stage_runner import (
    run_stage_with_retry,
)


def test_stage_runner_records_retry_attempts() -> None:

    pipeline_run_id = uuid4()

    started_at = datetime.now(
        UTC
    )

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
                f"stage-runner-test-{uuid4()}"
            ),
            started_at=started_at,
        )

        result = run_stage_with_retry(
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

        assert result == "success"

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    attempt,
                    status,
                    records_processed,
                    error_category
                FROM analytics.pipeline_stage_runs
                WHERE pipeline_run_id = %s
                ORDER BY attempt
                """,
                (
                    pipeline_run_id,
                ),
            )

            rows = cursor.fetchall()

    assert len(rows) == 2

    assert rows[0][0] == 1

    assert rows[0][1] == "FAILED"

    assert rows[0][2] is None

    assert rows[0][3] is not None

    assert rows[1][0] == 2

    assert rows[1][1] == "SUCCESS"

    assert rows[1][2] == 42

    assert rows[1][3] is None
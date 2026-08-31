from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.pipeline.repository import (
    start_pipeline_run,
)
from retailpulse.pipeline.stage_repository import (
    complete_stage_run,
    fail_stage_run,
    start_stage_run,
)


def test_pipeline_stage_run_can_be_started_and_completed() -> None:

    pipeline_run_id = uuid4()

    started_at = datetime.now(
        UTC
    )

    completed_at = datetime.now(
        UTC
    )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=(
                f"stage-repository-test-{uuid4()}"
            ),
            started_at=started_at,
        )

        stage_run_id = start_stage_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            stage_name="analytics_build",
            attempt=1,
            started_at=started_at,
        )

        complete_stage_run(
            connection,
            stage_run_id=stage_run_id,
            completed_at=completed_at,
            duration_ms=1250,
            records_processed=100,
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    status,
                    stage_name,
                    attempt,
                    completed_at,
                    duration_ms,
                    records_processed
                FROM analytics.pipeline_stage_runs
                WHERE stage_run_id = %s
                """,
                (stage_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == "SUCCESS"

    assert row[1] == "analytics_build"

    assert row[2] == 1

    assert row[3] == completed_at

    assert row[4] == 1250

    assert row[5] == 100


def test_pipeline_stage_run_can_be_failed() -> None:

    pipeline_run_id = uuid4()

    started_at = datetime.now(
        UTC
    )

    completed_at = datetime.now(
        UTC
    )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=(
                f"stage-repository-test-{uuid4()}"
            ),
            started_at=started_at,
        )

        stage_run_id = start_stage_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            stage_name="analytics_build",
            attempt=1,
            started_at=started_at,
        )

        fail_stage_run(
            connection,
            stage_run_id=stage_run_id,
            completed_at=completed_at,
            duration_ms=900,
            records_processed=50,
            error_category="TRANSIENT",
            error_message=(
                "Temporary database failure"
            ),
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    status,
                    error_category,
                    error_message,
                    duration_ms,
                    records_processed
                FROM analytics.pipeline_stage_runs
                WHERE stage_run_id = %s
                """,
                (stage_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == "FAILED"

    assert row[1] == "TRANSIENT"

    assert row[2] == (
        "Temporary database failure"
    )

    assert row[3] == 900

    assert row[4] == 50
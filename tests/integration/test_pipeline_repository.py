from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.pipeline.repository import (
    complete_pipeline_run,
    start_pipeline_run,
)


def test_pipeline_run_can_be_started_and_completed() -> None:

    pipeline_run_id = uuid4()

    logical_run_id = (
        f"repository-test-{uuid4()}"
    )

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
            logical_run_id=logical_run_id,
            started_at=started_at,
        )

        batch_id = uuid4()

        complete_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            batch_id=batch_id,
            orders_loaded=20,
            order_items_loaded=50,
            analytics_rows=100,
            started_at=started_at,
            completed_at=completed_at,
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    status,
                    batch_id,
                    orders_loaded,
                    order_items_loaded,
                    analytics_rows
                FROM analytics.pipeline_runs
                WHERE pipeline_run_id = %s
                """,
                (pipeline_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == "SUCCESS"

    assert row[1] == batch_id

    assert row[2] == 20

    assert row[3] == 50

    assert row[4] == 100
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.batch_identity import (
    build_batch_id,
)
from retailpulse.generators.ingestion_repository import (
    complete_batch,
    start_batch,
)
from retailpulse.observability.metrics_repository import (
    get_batch_metrics,
    list_batch_summaries,
)


def test_batch_metrics_can_be_read() -> None:

    logical_run_id = (
        f"metrics-test-{uuid4()}"
    )

    batch_id = build_batch_id(
        source_system="retailpulse_test",
        batch_type="ORDER_TRANSACTION",
        logical_run_id=logical_run_id,
    )

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        complete_batch(
            connection,
            batch_id,
            record_count=100,
        )

        metrics = get_batch_metrics(
            connection,
            batch_id=batch_id,
        )

        assert metrics is not None

        assert metrics.batch_id == batch_id

        assert metrics.status == "COMPLETED"

        assert metrics.record_count == 100

        assert metrics.attempt_count == 1

        assert metrics.completed_parts == 0

        assert metrics.failed_parts == 0

        assert metrics.total_parts == 0

        assert metrics.quality_checks == 0

        assert metrics.quality_failures == 0

        assert metrics.duration_seconds is not None

        assert metrics.duration_seconds >= 0

        assert metrics.orders_per_second is not None

        assert metrics.orders_per_second > 0

def test_batch_summaries_can_be_listed() -> None:

    logical_run_id = (
        f"list-test-{uuid4()}"
    )

    batch_id = build_batch_id(
        source_system="retailpulse_test",
        batch_type="ORDER_TRANSACTION",
        logical_run_id=logical_run_id,
    )

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        complete_batch(
            connection,
            batch_id,
            record_count=50,
        )

        batches = list_batch_summaries(
            connection,
            limit=10,
        )

    matching = [
        batch
        for batch in batches
        if batch.batch_id == batch_id
    ]

    assert len(matching) == 1

    batch = matching[0]

    assert batch.status == "COMPLETED"

    assert batch.record_count == 50
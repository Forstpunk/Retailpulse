from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.batch_identity import (
    build_batch_id,
)
from retailpulse.generators.ingestion_observability import (
    get_batch_parts_summary,
    get_batch_summary,
    get_failed_parts,
    get_failed_quality_checks,
    get_quality_summary,
)
from retailpulse.generators.ingestion_repository import (
    complete_batch,
    start_batch,
)


def test_ingestion_observability_reads_batch_state() -> None:

    logical_run_id = (
        f"observability-test-{uuid4()}"
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
            100,
        )

        batch = get_batch_summary(
            connection,
            batch_id=batch_id,
        )

        assert batch is not None

        assert batch.batch_id == batch_id
        assert batch.source_system == (
            "retailpulse_test"
        )
        assert batch.batch_type == (
            "ORDER_TRANSACTION"
        )
        assert batch.status == "COMPLETED"
        assert batch.record_count == 100
        assert batch.attempt_count == 1
        assert batch.max_attempts == 3

        assert batch.completed_at is not None

        assert (
            batch.duration_seconds is not None
        )

        parts = get_batch_parts_summary(
            connection,
            batch_id=batch_id,
        )

        assert parts == []

        failed_parts = get_failed_parts(
            connection,
            batch_id=batch_id,
        )

        assert failed_parts == []

        quality = get_quality_summary(
            connection,
            batch_id=batch_id,
        )

        assert quality == []

        failed_quality = (
            get_failed_quality_checks(
                connection,
                batch_id=batch_id,
            )
        )

        assert failed_quality == []
from uuid import uuid4

from retailpulse.common.database import get_connection
from retailpulse.generators.ingestion_repository import (
    fail_batch,
    get_batch,
    retry_failed_batch,
    start_batch,
)


def test_new_batch_can_be_started() -> None:
    batch_id = uuid4()

    with get_connection() as connection:
        claimed = start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        assert claimed is True

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None
        assert batch.status == "STARTED"
        assert batch.attempt_count == 1


def test_same_batch_cannot_be_started_twice() -> None:
    batch_id = uuid4()

    with get_connection() as connection:

        first = start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        second = start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        assert first is True
        assert second is False


def test_different_batches_are_independent() -> None:
    batch_a = uuid4()
    batch_b = uuid4()

    with get_connection() as connection:

        result_a = start_batch(
            connection,
            batch_a,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        result_b = start_batch(
            connection,
            batch_b,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        assert result_a is True
        assert result_b is True

def test_completed_batch_cannot_be_restarted() -> None:
    batch_id = uuid4()

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        from retailpulse.generators.ingestion_repository import (
            complete_batch,
        )

        complete_batch(
            connection,
            batch_id,
            100,
        )

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        ) is False

def test_failed_batch_can_be_retried() -> None:
    batch_id = uuid4()

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        fail_batch(
            connection,
            batch_id,
            "simulated failure",
        )

        retried = retry_failed_batch(
            connection,
            batch_id,
        )

        assert retried is True

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None
        assert batch.status == "STARTED"
        assert batch.attempt_count == 2
        assert batch.error_message is None

def test_failed_batch_stops_after_max_attempts() -> None:
    batch_id = uuid4()

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        for attempt in range(1, 4):

            fail_batch(
                connection,
                batch_id,
                f"failure {attempt}",
            )

            if attempt < 3:
                assert retry_failed_batch(
                    connection,
                    batch_id,
                    max_attempts=3,
                ) is True

        assert retry_failed_batch(
            connection,
            batch_id,
            max_attempts=3,
        ) is False

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None
        assert batch.status == "FAILED"
        assert batch.attempt_count == 3
from uuid import uuid4

from retailpulse.common.database import get_connection
from retailpulse.generators.ingestion_repository import (
    get_batch,
    start_batch,
)


def test_batch_claim_is_idempotent() -> None:
    batch_id = uuid4()

    with get_connection() as connection:

        first_claim = start_batch(
            connection,
            batch_id,
            "retailpulse_generator",
            "ORDER_TRANSACTION",
        )

        second_claim = start_batch(
            connection,
            batch_id,
            "retailpulse_generator",
            "ORDER_TRANSACTION",
        )

        assert first_claim is True
        assert second_claim is False

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None
        assert batch.status == "STARTED"
        assert batch.attempt_count == 1
from uuid import UUID

from psycopg import Connection

from retailpulse.generators.ingestion_repository import (
    get_batch,
    start_batch,
)


def claim_batch(
    connection: Connection,
    batch_id: UUID,
    source_system: str,
    batch_type: str,
) -> bool:
    """
    Claim a batch for processing.

    Returns:
        True  -> caller should process the batch.
        False -> batch should not be processed.
    """

    existing = get_batch(
        connection,
        batch_id,
    )

    if existing is None:
        return start_batch(
            connection,
            batch_id,
            source_system,
            batch_type,
        )

    if existing.status == "COMPLETED":
        return False

    if existing.status == "STARTED":
        raise RuntimeError(
            f"Batch {batch_id} is already in progress"
        )

    if existing.status == "FAILED":
        raise RuntimeError(
            f"Batch {batch_id} previously failed "
            "and requires explicit retry handling"
        )

    raise RuntimeError(
        f"Unknown ingestion batch status: "
        f"{existing.status}"
    )
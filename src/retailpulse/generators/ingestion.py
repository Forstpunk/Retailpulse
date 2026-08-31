from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class IngestionBatch:
    batch_id: UUID
    source_system: str
    batch_type: str


def create_ingestion_batch(
    *,
    source_system: str,
    batch_type: str,
) -> IngestionBatch:
    return IngestionBatch(
        batch_id=uuid4(),
        source_system=source_system,
        batch_type=batch_type,
    )
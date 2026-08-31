from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class IngestionMetrics:
    batch_id: UUID
    status: str

    record_count: int
    order_item_count: int

    attempt_count: int
    physical_batch_count: int

    started_at: datetime
    completed_at: datetime | None

    duration_seconds: float | None
    records_per_second: float | None

    failed: bool
    quality_passed: bool | None
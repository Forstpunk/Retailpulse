from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class IngestionMetrics:
    batch_id: str
    source_system: str
    batch_type: str

    started_at: datetime
    completed_at: datetime

    orders_generated: int
    orders_loaded: int
    order_items_loaded: int

    physical_batches: int

    duration_seconds: Decimal

    @property
    def throughput_orders_per_second(
        self,
    ) -> Decimal:
        if self.duration_seconds <= 0:
            return Decimal(0)

        return (
            Decimal(self.orders_loaded)
            / self.duration_seconds
        )
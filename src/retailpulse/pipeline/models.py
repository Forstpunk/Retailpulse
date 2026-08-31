from dataclasses import dataclass
from enum import StrEnum

from retailpulse.pipeline.errors import (
    PipelineErrorCategory,
)


class PipelineStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    # A logical run that was not executed because a
    # pipeline_runs row for its logical_run_id already
    # existed (SUCCESS/RUNNING/FAILED). See
    # DuplicateLogicalRunError and run_pipeline().
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class PipelineResult:
    status: PipelineStatus

    pipeline_run_id: str

    logical_run_id: str

    ingestion_completed: bool

    quality_passed: bool

    analytics_completed: bool

    batch_id: str | None

    orders_loaded: int

    order_items_loaded: int

    analytics_rows: int

    error_category: (
        PipelineErrorCategory | None
    )

    message: str

    @property
    def succeeded(self) -> bool:
        return (
            self.status
            == PipelineStatus.SUCCESS
        )
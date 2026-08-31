from uuid import UUID

from psycopg import Connection

from retailpulse.quality.checks import (
    run_transaction_quality_checks,
)
from retailpulse.quality.repository import (
    persist_quality_report,
)


def run_and_persist_transaction_quality(
    connection: Connection,
    *,
    batch_id: UUID,
    start_order_id: int,
    expected_order_count: int,
    expected_order_item_count: int | None = None,
    pipeline_run_id: UUID | None = None,
) -> bool:
    """
    Run transaction quality checks and persist
    the resulting quality report.

    Returns True only when every quality check passes.
    """

    report = run_transaction_quality_checks(
        connection,
        start_order_id=start_order_id,
        expected_order_count=expected_order_count,
        expected_order_item_count=(
            expected_order_item_count
        ),
    )

    persist_quality_report(
        connection,
        batch_id=batch_id,
        report=report,
        pipeline_run_id=pipeline_run_id,
    )

    return report.passed
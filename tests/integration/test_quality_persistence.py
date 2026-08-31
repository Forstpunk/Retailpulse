from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.batch_identity import (
    build_batch_id,
)
from retailpulse.generators.ingestion_repository import (
    start_batch,
)
from retailpulse.quality.models import (
    QualityCheckResult,
    QualityCheckType,
    QualityReport,
    QualityStatus,
)
from retailpulse.quality.repository import (
    get_quality_results,
    persist_quality_report,
)


def test_quality_report_can_be_persisted() -> None:

    logical_run_id = (
        f"quality-test-{uuid4()}"
    )

    batch_id = build_batch_id(
        source_system="retailpulse_test",
        batch_type="ORDER_TRANSACTION",
        logical_run_id=logical_run_id,
    )

    report = QualityReport(
        checks=(
            QualityCheckResult(
                check_name="order_count",
                status=QualityStatus.PASS,
                observed_value=100,
                expected_value=100,
                message=(
                    "Order count matches expected count"
                ),
                check_type=(
                    QualityCheckType.COMPLETENESS
                ),
            ),
            QualityCheckResult(
                check_name="orphan_order_items",
                status=QualityStatus.PASS,
                observed_value=0,
                expected_value=0,
                message=(
                    "No orphan order items found"
                ),
                check_type=(
                    QualityCheckType.REFERENTIAL_INTEGRITY
                ),
            ),
        )
    )

    with get_connection() as connection:

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        persist_quality_report(
            connection,
            batch_id=batch_id,
            report=report,
        )

        results = get_quality_results(
            connection,
            batch_id=batch_id,
        )

    assert len(results) == 2

    assert results[0].check_name == (
        "order_count"
    )

    assert results[0].status == (
        QualityStatus.PASS
    )

    assert results[0].check_type == (
        QualityCheckType.COMPLETENESS
    )

    assert results[1].check_name == (
        "orphan_order_items"
    )

    assert results[1].observed_value == "0"

    assert results[1].check_type == (
        QualityCheckType.REFERENTIAL_INTEGRITY
    )


def test_quality_report_can_be_linked_to_a_pipeline_run() -> None:

    from retailpulse.pipeline.repository import (
        start_pipeline_run,
    )

    logical_run_id = (
        f"quality-pipeline-link-test-{uuid4()}"
    )

    batch_id = build_batch_id(
        source_system="retailpulse_test",
        batch_type="ORDER_TRANSACTION",
        logical_run_id=logical_run_id,
    )

    pipeline_run_id = uuid4()

    report = QualityReport(
        checks=(
            QualityCheckResult(
                check_name="order_financials",
                status=QualityStatus.PASS,
                observed_value=0,
                expected_value=0,
                message=(
                    "Order financial totals reconcile"
                ),
                check_type=(
                    QualityCheckType.FINANCIAL_CONSISTENCY
                ),
            ),
        )
    )

    with get_connection() as connection:

        start_pipeline_run(
            connection,
            pipeline_run_id=pipeline_run_id,
            logical_run_id=logical_run_id,
            started_at=datetime.now(
                UTC
            ),
        )

        assert start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        persist_quality_report(
            connection,
            batch_id=batch_id,
            report=report,
            pipeline_run_id=pipeline_run_id,
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT pipeline_run_id, severity
                FROM retail.ingestion_quality_results
                WHERE batch_id = %s
                """,
                (batch_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == pipeline_run_id

    assert row[1] == "ERROR"
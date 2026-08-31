from uuid import UUID

from psycopg import Connection

from retailpulse.quality.models import (
    QualityCheckResult,
    QualityCheckType,
    QualityReport,
    QualitySeverity,
    QualityStatus,
)


def persist_quality_report(
    connection: Connection,
    *,
    batch_id: UUID,
    report: QualityReport,
    pipeline_run_id: UUID | None = None,
) -> None:
    """
    Persist all quality-check results for a logical
    ingestion batch, linked to the pipeline run that
    produced them (when known).

    The caller owns the transaction boundary.
    """

    with connection.cursor() as cursor:

        for check in report.checks:

            cursor.execute(
                """
                INSERT INTO retail.ingestion_quality_results (
                    batch_id,
                    pipeline_run_id,
                    check_name,
                    check_type,
                    severity,
                    status,
                    observed_value,
                    expected_value,
                    message
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    batch_id,
                    pipeline_run_id,
                    check.check_name,
                    check.check_type.value,
                    check.severity.value,
                    check.status.value,
                    str(check.observed_value),
                    (
                        None
                        if check.expected_value is None
                        else str(
                            check.expected_value
                        )
                    ),
                    check.message,
                ),
            )


def get_quality_results(
    connection: Connection,
    *,
    batch_id: UUID,
) -> list[QualityCheckResult]:
    """
    Retrieve persisted quality results for a batch.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                check_name,
                status,
                observed_value,
                expected_value,
                message,
                check_type,
                severity
            FROM retail.ingestion_quality_results
            WHERE batch_id = %s
            ORDER BY quality_result_id
            """,
            (batch_id,),
        )

        rows = cursor.fetchall()

    return [
        QualityCheckResult(
            check_name=row[0],
            status=QualityStatus(row[1]),
            observed_value=row[2],
            expected_value=row[3],
            message=row[4],
            check_type=QualityCheckType(row[5]),
            severity=QualitySeverity(row[6]),
        )
        for row in rows
    ]
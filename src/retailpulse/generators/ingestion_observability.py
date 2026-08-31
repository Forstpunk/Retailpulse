from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection


@dataclass(frozen=True)
class BatchSummary:
    batch_id: UUID
    source_system: str
    batch_type: str
    status: str
    record_count: int
    attempt_count: int
    max_attempts: int
    started_at: datetime
    completed_at: datetime | None
    last_attempt_at: datetime
    last_heartbeat_at: datetime
    error_message: str | None

    @property
    def duration_seconds(self) -> float | None:
        if self.completed_at is None:
            return None

        return (
            self.completed_at
            - self.started_at
        ).total_seconds()


@dataclass(frozen=True)
class BatchPartSummary:
    batch_id: UUID
    part_number: int
    status: str
    record_count: int
    order_item_count: int
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    start_order_id: int | None
    start_order_item_id: int | None

    @property
    def duration_seconds(self) -> float | None:
        if self.completed_at is None:
            return None

        return (
            self.completed_at
            - self.started_at
        ).total_seconds()


@dataclass(frozen=True)
class QualitySummary:
    check_name: str
    status: str
    observed_value: str | None
    expected_value: str | None
    message: str | None
    checked_at: datetime


def get_batch_summary(
    connection: Connection,
    *,
    batch_id: UUID,
) -> BatchSummary | None:
    """
    Return the operational summary for one logical
    ingestion batch.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                batch_id,
                source_system,
                batch_type,
                status,
                record_count,
                attempt_count,
                max_attempts,
                started_at,
                completed_at,
                last_attempt_at,
                last_heartbeat_at,
                error_message
            FROM retail.ingestion_batches
            WHERE batch_id = %s
            """,
            (batch_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return BatchSummary(
        batch_id=row[0],
        source_system=row[1],
        batch_type=row[2],
        status=row[3],
        record_count=row[4],
        attempt_count=row[5],
        max_attempts=row[6],
        started_at=row[7],
        completed_at=row[8],
        last_attempt_at=row[9],
        last_heartbeat_at=row[10],
        error_message=row[11],
    )


def get_batch_parts_summary(
    connection: Connection,
    *,
    batch_id: UUID,
) -> list[BatchPartSummary]:
    """
    Return all physical ingestion parts for a logical batch.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                batch_id,
                part_number,
                status,
                record_count,
                order_item_count,
                started_at,
                completed_at,
                error_message,
                start_order_id,
                start_order_item_id
            FROM retail.ingestion_batch_parts
            WHERE batch_id = %s
            ORDER BY part_number
            """,
            (batch_id,),
        )

        rows = cursor.fetchall()

    return [
        BatchPartSummary(
            batch_id=row[0],
            part_number=row[1],
            status=row[2],
            record_count=row[3],
            order_item_count=row[4],
            started_at=row[5],
            completed_at=row[6],
            error_message=row[7],
            start_order_id=row[8],
            start_order_item_id=row[9],
        )
        for row in rows
    ]


def get_quality_summary(
    connection: Connection,
    *,
    batch_id: UUID,
) -> list[QualitySummary]:
    """
    Return all persisted quality results for a batch.
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
                checked_at
            FROM retail.ingestion_quality_results
            WHERE batch_id = %s
            ORDER BY quality_result_id
            """,
            (batch_id,),
        )

        rows = cursor.fetchall()

    return [
        QualitySummary(
            check_name=row[0],
            status=row[1],
            observed_value=row[2],
            expected_value=row[3],
            message=row[4],
            checked_at=row[5],
        )
        for row in rows
    ]


def get_failed_parts(
    connection: Connection,
    *,
    batch_id: UUID,
) -> list[BatchPartSummary]:
    """
    Return only physical parts that failed.
    """

    parts = get_batch_parts_summary(
        connection,
        batch_id=batch_id,
    )

    return [
        part
        for part in parts
        if part.status == "FAILED"
    ]


def get_failed_quality_checks(
    connection: Connection,
    *,
    batch_id: UUID,
) -> list[QualitySummary]:
    """
    Return only failed persisted quality checks.
    """

    checks = get_quality_summary(
        connection,
        batch_id=batch_id,
    )

    return [
        check
        for check in checks
        if check.status == "FAIL"
    ]
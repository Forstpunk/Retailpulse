from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection


@dataclass(frozen=True)
class BatchMetrics:
    batch_id: UUID

    status: str

    record_count: int

    attempt_count: int

    max_attempts: int

    started_at: datetime

    completed_at: datetime | None

    last_attempt_at: datetime

    last_heartbeat_at: datetime | None

    duration_seconds: float | None

    orders_per_second: float | None

    completed_parts: int

    failed_parts: int

    total_parts: int

    quality_checks: int

    quality_failures: int


def get_batch_metrics(
    connection: Connection,
    *,
    batch_id: UUID,
) -> BatchMetrics | None:
    """
    Read operational metrics for one logical
    ingestion batch.

    This function is read-only.

    It combines:

        ingestion_batches
        ingestion_batch_parts
        ingestion_quality_results
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                b.batch_id,
                b.status,
                b.record_count,
                b.attempt_count,
                b.max_attempts,
                b.started_at,
                b.completed_at,
                b.last_attempt_at,
                b.last_heartbeat_at,

                CASE
                    WHEN b.completed_at IS NOT NULL
                    THEN EXTRACT(
                        EPOCH FROM (
                            b.completed_at
                            - b.started_at
                        )
                    )
                    ELSE NULL
                END AS duration_seconds,

                COUNT(
                    DISTINCT CASE
                        WHEN p.status = 'COMPLETED'
                        THEN p.part_number
                    END
                ) AS completed_parts,

                COUNT(
                    DISTINCT CASE
                        WHEN p.status = 'FAILED'
                        THEN p.part_number
                    END
                ) AS failed_parts,

                COUNT(
                    DISTINCT p.part_number
                ) AS total_parts,

                COUNT(
                    DISTINCT q.quality_result_id
                ) AS quality_checks,

                COUNT(
                    DISTINCT CASE
                        WHEN q.status = 'FAIL'
                        THEN q.quality_result_id
                    END
                ) AS quality_failures

            FROM retail.ingestion_batches b

            LEFT JOIN retail.ingestion_batch_parts p
                ON p.batch_id = b.batch_id

            LEFT JOIN retail.ingestion_quality_results q
                ON q.batch_id = b.batch_id

            WHERE b.batch_id = %s

            GROUP BY
                b.batch_id,
                b.status,
                b.record_count,
                b.attempt_count,
                b.max_attempts,
                b.started_at,
                b.completed_at,
                b.last_attempt_at,
                b.last_heartbeat_at
            """,
            (batch_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    (
        row_batch_id,
        status,
        record_count,
        attempt_count,
        max_attempts,
        started_at,
        completed_at,
        last_attempt_at,
        last_heartbeat_at,
        duration_seconds,
        completed_parts,
        failed_parts,
        total_parts,
        quality_checks,
        quality_failures,
    ) = row

    orders_per_second = None

    if (
        duration_seconds is not None
        and duration_seconds > 0
        and record_count > 0
    ):
        orders_per_second = (
            record_count
            / float(duration_seconds)
        )

    return BatchMetrics(
        batch_id=row_batch_id,
        status=status,
        record_count=record_count,
        attempt_count=attempt_count,
        max_attempts=max_attempts,
        started_at=started_at,
        completed_at=completed_at,
        last_attempt_at=last_attempt_at,
        last_heartbeat_at=last_heartbeat_at,
        duration_seconds=(
            float(duration_seconds)
            if duration_seconds is not None
            else None
        ),
        orders_per_second=orders_per_second,
        completed_parts=completed_parts,
        failed_parts=failed_parts,
        total_parts=total_parts,
        quality_checks=quality_checks,
        quality_failures=quality_failures,
    )

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
    duration_seconds: float | None


def list_batch_summaries(
    connection: Connection,
    *,
    limit: int = 20,
) -> list[BatchSummary]:
    """
    Return the most recently created ingestion batches.

    This function is read-only.
    """

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero"
        )

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

                CASE
                    WHEN completed_at IS NOT NULL
                    THEN EXTRACT(
                        EPOCH FROM (
                            completed_at
                            - started_at
                        )
                    )
                    ELSE NULL
                END AS duration_seconds

            FROM retail.ingestion_batches

            ORDER BY created_at DESC

            LIMIT %s
            """,
            (limit,),
        )

        rows = cursor.fetchall()

    return [
        BatchSummary(
            batch_id=row[0],
            source_system=row[1],
            batch_type=row[2],
            status=row[3],
            record_count=row[4],
            attempt_count=row[5],
            max_attempts=row[6],
            started_at=row[7],
            completed_at=row[8],
            duration_seconds=(
                float(row[9])
                if row[9] is not None
                else None
            ),
        )
        for row in rows
    ]
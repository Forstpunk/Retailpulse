from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection


@dataclass(frozen=True)
class Watermark:
    pipeline_name: str
    source_name: str
    watermark_column: str
    watermark_value: str
    updated_at: datetime


def get_watermark(
    connection: Connection,
    *,
    pipeline_name: str,
    source_name: str,
) -> Watermark | None:
    """
    Read the current watermark for a (pipeline, source)
    pair. Returns None on the first run — the caller
    decides what "no watermark yet" means for its source
    (e.g. an integer id watermark starts at 0).
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                pipeline_name,
                source_name,
                watermark_column,
                watermark_value,
                updated_at
            FROM analytics.pipeline_watermarks
            WHERE pipeline_name = %s
              AND source_name = %s
            """,
            (
                pipeline_name,
                source_name,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return Watermark(
        pipeline_name=row[0],
        source_name=row[1],
        watermark_column=row[2],
        watermark_value=row[3],
        updated_at=row[4],
    )


def get_watermark_int(
    connection: Connection,
    *,
    pipeline_name: str,
    source_name: str,
    default: int = 0,
) -> int:
    """
    Convenience accessor for integer (id-based)
    watermarks, which is what every current source in
    RetailPulse uses.
    """

    watermark = get_watermark(
        connection,
        pipeline_name=pipeline_name,
        source_name=source_name,
    )

    if watermark is None:
        return default

    return int(watermark.watermark_value)


def advance_watermark(
    connection: Connection,
    *,
    pipeline_name: str,
    source_name: str,
    watermark_column: str,
    watermark_value: str,
) -> None:
    """
    Advance the watermark for a (pipeline, source) pair.

    Callers MUST only call this after the corresponding
    data has been fully and successfully processed
    (extracted, loaded, and reflected in downstream
    marts) — this function performs no validation of
    that invariant itself; it is a plain upsert.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO analytics.pipeline_watermarks (
                pipeline_name,
                source_name,
                watermark_column,
                watermark_value,
                updated_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (pipeline_name, source_name)
            DO UPDATE
            SET
                watermark_column =
                    EXCLUDED.watermark_column,
                watermark_value =
                    EXCLUDED.watermark_value,
                updated_at =
                    CURRENT_TIMESTAMP
            """,
            (
                pipeline_name,
                source_name,
                watermark_column,
                watermark_value,
            ),
        )

from uuid import uuid4

from retailpulse.analytics.watermark_repository import (
    advance_watermark,
    get_watermark,
    get_watermark_int,
)
from retailpulse.common.database import (
    get_connection,
)


def test_get_watermark_returns_none_when_absent() -> None:

    source_name = f"unit-test-source-{uuid4()}"

    with get_connection() as connection:

        watermark = get_watermark(
            connection,
            pipeline_name="unit-test-pipeline",
            source_name=source_name,
        )

    assert watermark is None


def test_get_watermark_int_returns_default_when_absent() -> None:

    source_name = f"unit-test-source-{uuid4()}"

    with get_connection() as connection:

        value = get_watermark_int(
            connection,
            pipeline_name="unit-test-pipeline",
            source_name=source_name,
            default=0,
        )

    assert value == 0


def test_advance_watermark_then_read_back() -> None:

    pipeline_name = f"unit-test-pipeline-{uuid4()}"

    source_name = "unit-test-source"

    with get_connection() as connection:

        advance_watermark(
            connection,
            pipeline_name=pipeline_name,
            source_name=source_name,
            watermark_column="order_id",
            watermark_value="100",
        )

    with get_connection() as connection:

        watermark = get_watermark(
            connection,
            pipeline_name=pipeline_name,
            source_name=source_name,
        )

    assert watermark is not None

    assert watermark.watermark_column == "order_id"

    assert watermark.watermark_value == "100"


def test_advance_watermark_upserts_the_same_scope() -> None:

    pipeline_name = f"unit-test-pipeline-{uuid4()}"

    source_name = "unit-test-source"

    with get_connection() as connection:

        advance_watermark(
            connection,
            pipeline_name=pipeline_name,
            source_name=source_name,
            watermark_column="order_id",
            watermark_value="100",
        )

        advance_watermark(
            connection,
            pipeline_name=pipeline_name,
            source_name=source_name,
            watermark_column="order_id",
            watermark_value="250",
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.pipeline_watermarks
                WHERE pipeline_name = %s
                  AND source_name = %s
                """,
                (
                    pipeline_name,
                    source_name,
                ),
            )

            row_count = cursor.fetchone()[0]

    assert row_count == 1

    with get_connection() as connection:

        value = get_watermark_int(
            connection,
            pipeline_name=pipeline_name,
            source_name=source_name,
        )

    assert value == 250

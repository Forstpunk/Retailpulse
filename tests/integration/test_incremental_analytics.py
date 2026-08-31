from uuid import uuid4

import pytest

import retailpulse.analytics.build as build_module
from retailpulse.analytics.build import (
    ORDERS_SOURCE,
    PIPELINE_NAME,
    build_analytics,
)
from retailpulse.analytics.watermark_repository import (
    get_watermark_int,
)
from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.generators.transaction_ingestion import (
    run_transaction_ingestion,
)


def _small_config(orders: int) -> GeneratorConfig:

    return GeneratorConfig(
        seed=2026,
        categories=10,
        suppliers=10,
        stores=5,
        products=50,
        customers=100,
        orders=orders,
        order_items=orders * 2,
        payments=orders,
        returns=1,
        batch_size=10,
    )


def test_second_build_analytics_call_processes_no_new_orders() -> None:

    logical_run_id = (
        f"incremental-analytics-{uuid4()}"
    )

    with get_connection() as connection:

        run_transaction_ingestion(
            connection,
            _small_config(orders=6),
            logical_run_id=logical_run_id,
        )

    with get_connection() as connection:

        first_result = build_analytics(
            connection
        )

    assert first_result.orders_loaded >= 6

    with get_connection() as connection:

        watermark_after_first = (
            get_watermark_int(
                connection,
                pipeline_name=PIPELINE_NAME,
                source_name=ORDERS_SOURCE,
            )
        )

    with get_connection() as connection, connection.cursor() as cursor:

        cursor.execute(
            "SELECT MAX(order_id) "
            "FROM retail.orders"
        )

        max_order_id = (
            cursor.fetchone()[0]
        )

    assert (
        watermark_after_first
        == max_order_id
    )

    # No new orders were ingested between the two calls,
    # so the second call must process exactly zero.

    with get_connection() as connection:

        second_result = build_analytics(
            connection
        )

    assert second_result.orders_loaded == 0

    assert (
        second_result.order_items_loaded
        == 0
    )


def test_watermark_does_not_advance_when_mart_refresh_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    logical_run_id = (
        f"incremental-failure-{uuid4()}"
    )

    with get_connection() as connection:

        run_transaction_ingestion(
            connection,
            _small_config(orders=4),
            logical_run_id=logical_run_id,
        )

    with get_connection() as connection:

        watermark_before = get_watermark_int(
            connection,
            pipeline_name=PIPELINE_NAME,
            source_name=ORDERS_SOURCE,
        )

    def failing_mart_refresh(
        connection,
    ) -> int:

        raise RuntimeError(
            "simulated mart refresh failure"
        )

    monkeypatch.setattr(
        build_module,
        "refresh_daily_sales",
        failing_mart_refresh,
    )

    with pytest.raises(RuntimeError), get_connection() as connection:

        build_analytics(connection)

    with get_connection() as connection:

        watermark_after = get_watermark_int(
            connection,
            pipeline_name=PIPELINE_NAME,
            source_name=ORDERS_SOURCE,
        )

    assert (
        watermark_after
        == watermark_before
    )

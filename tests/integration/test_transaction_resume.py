from dataclasses import replace
from uuid import uuid4

import pytest

from retailpulse.common.database import get_connection
from retailpulse.generators.config import DEV_CONFIG
from retailpulse.generators.ingestion_parts_repository import (
    get_batch_part_start_ids,
    get_completed_batch_parts,
)
from retailpulse.generators.ingestion_repository import (
    get_batch,
)
from retailpulse.generators.transaction_ingestion import (
    run_transaction_ingestion,
)


def test_failed_transaction_batch_can_resume() -> None:
    """
    Verify that a failed logical transaction batch can be
    retried and resumed without duplicating completed
    physical batches.
    """

    logical_run_id = (
        f"resume-test-{uuid4()}"
    )

    config = replace(
        DEV_CONFIG,
        orders=25,
        batch_size=10,
    )

    # =========================================================
    # 1. First execution
    #
    # Part 1 should complete.
    # Part 2 should fail intentionally.
    # Parts 3+ should never be processed.
    # =========================================================

    with get_connection() as connection, pytest.raises(RuntimeError):

        run_transaction_ingestion(
            connection,
            config,
            logical_run_id=logical_run_id,
            fail_part=2,
        )

    # =========================================================
    # 2. Verify logical batch is FAILED
    # =========================================================

    with get_connection() as connection:

        # Reconstruct the deterministic batch ID by
        # executing the same identity function used by
        # the ingestion runner.
        from retailpulse.generators.batch_identity import (
            build_batch_id,
        )

        batch_id = build_batch_id(
            source_system="retailpulse_generator",
            batch_type="ORDER_TRANSACTION",
            logical_run_id=logical_run_id,
        )

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None

        assert batch.status == "FAILED"

        # -----------------------------------------------------
        # Physical checkpoint state
        # -----------------------------------------------------

        completed_parts = (
            get_completed_batch_parts(
                connection,
                batch_id=batch_id,
            )
        )

        assert 1 in completed_parts

        assert completed_parts[1]["orders"] == 10

        assert 2 not in completed_parts

        # -----------------------------------------------------
        # Verify original source IDs were persisted
        # -----------------------------------------------------

        start_ids = (
            get_batch_part_start_ids(
                connection,
                batch_id=batch_id,
            )
        )

        assert start_ids is not None

        start_order_id, start_order_item_id = (
            start_ids
        )

        assert start_order_id > 0
        assert start_order_item_id > 0

        # -----------------------------------------------------
        # Verify only Part 1 reached PostgreSQL
        # -----------------------------------------------------

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM retail.orders
                WHERE order_id >= %s
                  AND order_id < %s
                """,
                (
                    start_order_id,
                    start_order_id + 25,
                ),
            )

            orders_after_failure = (
                cursor.fetchone()[0]
            )

        assert orders_after_failure == 10

    # =========================================================
    # 3. Retry the SAME logical batch
    #
    # Important:
    #
    # Same logical_run_id
    #        ↓
    # Same batch_id
    #        ↓
    # Existing FAILED batch
    #        ↓
    # retry_failed_batch()
    #        ↓
    # Part 1 is skipped
    # Part 2 is retried
    # Parts 3+ are processed
    # =========================================================

    result = None

    with get_connection() as connection:

        result = run_transaction_ingestion(
            connection,
            config,
            logical_run_id=logical_run_id,
        )

    assert result is not None

    assert result["orders"] == 25

    assert result["order_items"] > 25

    # =========================================================
    # 4. Verify final logical batch state
    # =========================================================

    with get_connection() as connection:

        batch = get_batch(
            connection,
            batch_id,
        )

        assert batch is not None

        assert batch.status == "COMPLETED"

        assert batch.record_count == 25

        # =====================================================
        # 5. Verify all physical batches completed
        # =====================================================

        completed_parts = (
            get_completed_batch_parts(
                connection,
                batch_id=batch_id,
            )
        )

        assert set(
            completed_parts.keys()
        ) == {1, 2, 3}

        assert (
            completed_parts[1]["orders"]
            == 10
        )

        assert (
            completed_parts[2]["orders"]
            == 10
        )

        assert (
            completed_parts[3]["orders"]
            == 5
        )

        # =====================================================
        # 6. Verify total physical records
        # =====================================================

        total_orders = sum(
            part["orders"]
            for part in completed_parts.values()
        )

        total_order_items = sum(
            part["order_items"]
            for part in completed_parts.values()
        )

        assert total_orders == 25

        assert total_order_items == (
            result["order_items"]
        )

        # =====================================================
        # 7. Verify PostgreSQL contains exactly 25 orders
        # =====================================================

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM retail.orders
                WHERE order_id >= %s
                  AND order_id < %s
                """,
                (
                    start_order_id,
                    start_order_id + 25,
                ),
            )

            final_order_count = (
                cursor.fetchone()[0]
            )

        assert final_order_count == 25

        # =====================================================
        # 8. Verify no duplicate order IDs
        # =====================================================

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT order_id
                    FROM retail.orders
                    WHERE order_id >= %s
                      AND order_id < %s
                    GROUP BY order_id
                    HAVING COUNT(*) > 1
                ) duplicates
                """,
                (
                    start_order_id,
                    start_order_id + 25,
                ),
            )

            duplicate_orders = (
                cursor.fetchone()[0]
            )

        assert duplicate_orders == 0

        # =====================================================
        # 9. Verify physical part 1 was not regenerated
        # =====================================================

        assert (
            completed_parts[1]["orders"]
            == 10
        )
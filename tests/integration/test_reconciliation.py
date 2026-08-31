from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.batch_identity import (
    build_batch_id,
)
from retailpulse.generators.ingestion_parts_repository import (
    complete_batch_part,
    start_batch_part,
)
from retailpulse.generators.ingestion_repository import (
    start_batch,
)
from retailpulse.generators.repositories import (
    get_customer_ids,
    get_next_order_id,
    get_next_order_item_id,
    get_product_prices,
    get_store_ids,
)
from retailpulse.generators.transaction_generator import (
    generate_transactions,
)
from retailpulse.generators.transaction_loader import (
    load_transaction_batch,
)
from retailpulse.quality.reconciliation import (
    reconcile_transaction_batch,
)


def test_transaction_reconciliation() -> None:

    logical_run_id = (
        f"reconciliation-test-{uuid4()}"
    )

    batch_id = build_batch_id(
        source_system="retailpulse_test",
        batch_type="ORDER_TRANSACTION",
        logical_run_id=logical_run_id,
    )

    with get_connection() as connection:

        customer_ids = get_customer_ids(
            connection
        )

        store_ids = get_store_ids(
            connection
        )

        product_prices = get_product_prices(
            connection
        )

        assert customer_ids
        assert store_ids
        assert product_prices

        start_order_id = (
            get_next_order_id(
                connection
            )
        )

        start_order_item_id = (
            get_next_order_item_id(
                connection
            )
        )

        transactions = generate_transactions(
            start_order_id=start_order_id,
            start_order_item_id=start_order_item_id,
            count=5,
            customer_ids=customer_ids,
            store_ids=store_ids,
            product_prices=product_prices,
            seed=12345,
            start_date=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
            end_date=datetime(
                2026,
                12,
                31,
                23,
                59,
                59,
                tzinfo=UTC,
            ),
        )

        batch = list(transactions)

        assert len(batch) == 5

        expected_order_items = sum(
            len(transaction.items)
            for transaction in batch
        )

        claimed = start_batch(
            connection,
            batch_id,
            "retailpulse_test",
            "ORDER_TRANSACTION",
        )

        assert claimed is True

        start_batch_part(
            connection,
            batch_id=batch_id,
            part_number=1,
            start_order_id=start_order_id,
            start_order_item_id=start_order_item_id,
        )

        orders_loaded, items_loaded = (
            load_transaction_batch(
                connection,
                batch,
            )
        )

        assert orders_loaded == 5

        assert (
            items_loaded
            == expected_order_items
        )

        with connection.transaction():

            complete_batch_part(
                connection,
                batch_id=batch_id,
                part_number=1,
                record_count=orders_loaded,
                order_item_count=items_loaded,
            )

        result = (
            reconcile_transaction_batch(
                connection,
                batch_id=batch_id,
                start_order_id=start_order_id,
                expected_orders=orders_loaded,
                expected_order_items=items_loaded,
            )
        )

        assert result.passed is True

        assert (
            result.actual_orders
            == orders_loaded
        )

        assert (
            result.actual_order_items
            == items_loaded
        )

        assert (
            result.duplicate_order_ids == 0
        )

        assert (
            result.duplicate_order_item_ids
            == 0
        )

        assert (
            result.orphan_order_items == 0
        )

        assert (
            result.order_financial_mismatches
            == 0
        )
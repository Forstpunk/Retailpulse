from datetime import UTC, datetime

from retailpulse.common.database import get_connection
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


def test_transaction_batch_loads_successfully() -> None:
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

        assert customer_ids, (
            "Expected customers to exist"
        )

        assert store_ids, (
            "Expected stores to exist"
        )

        assert product_prices, (
            "Expected products to exist"
        )

        # -----------------------------------------------------
        # Determine a fresh ID range
        # -----------------------------------------------------

        start_order_id = get_next_order_id(
            connection
        )

        start_order_item_id = (
            get_next_order_item_id(
                connection
            )
        )

        # -----------------------------------------------------
        # Generate transactions
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Load transaction batch
        # -----------------------------------------------------

        orders_loaded, items_loaded = (
            load_transaction_batch(
                connection,
                batch,
            )
        )

        assert orders_loaded == 5
        assert items_loaded > 0

        # -----------------------------------------------------
        # Verify orders
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
                    start_order_id + 5,
                ),
            )

            orders_after = (
                cursor.fetchone()[0]
            )

        assert orders_after == 5

        # -----------------------------------------------------
        # Verify order items
        # -----------------------------------------------------

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM retail.order_items
                WHERE order_id >= %s
                  AND order_id < %s
                """,
                (
                    start_order_id,
                    start_order_id + 5,
                ),
            )

            order_items_after = (
                cursor.fetchone()[0]
            )

        assert (
            order_items_after
            == items_loaded
        )
from datetime import datetime
from decimal import Decimal

from retailpulse.generators.transaction_batches import (
    batch_transactions,
)
from retailpulse.generators.transaction_generator import (
    generate_transactions,
)


def create_transactions():
    return generate_transactions(
        start_order_id=1,
        start_order_item_id=1,
        count=25,
        customer_ids=[1, 2, 3],
        store_ids=[1, 2],
        product_prices={
            1: Decimal("100.00"),
            2: Decimal("200.00"),
            3: Decimal("300.00"),
        },
        seed=42,
        start_date=datetime(
            2026,
            1,
            1,
        ),
        end_date=datetime(
            2026,
            12,
            31,
        ),
    )


def test_transactions_are_batched():
    batches = list(
        batch_transactions(
            create_transactions(),
            batch_size=10,
        )
    )

    assert len(batches) == 3

    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5


def test_batching_preserves_all_transactions():
    batches = list(
        batch_transactions(
            create_transactions(),
            batch_size=7,
        )
    )

    transactions = [
        transaction
        for batch in batches
        for transaction in batch
    ]

    assert len(transactions) == 25

    assert [
        transaction.order.order_id
        for transaction in transactions
    ] == list(range(1, 26))


def test_invalid_batch_size_is_rejected():
    transactions = create_transactions()

    try:
        list(
            batch_transactions(
                transactions,
                batch_size=0,
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )
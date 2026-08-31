from datetime import datetime
from decimal import Decimal

from retailpulse.generators.transaction_generator import (
    generate_transactions,
)


def test_order_item_ids_are_globally_unique():
    transactions = list(
        generate_transactions(
            start_order_id=1,
            start_order_item_id=1,
            count=100,
            customer_ids=[1, 2, 3, 4, 5],
            store_ids=[1, 2],
            product_prices={
                1: Decimal("100.00"),
                2: Decimal("200.00"),
                3: Decimal("300.00"),
                4: Decimal("400.00"),
                5: Decimal("500.00"),
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
    )

    item_ids = [
        item.order_item_id
        for transaction in transactions
        for item in transaction.items
    ]

    assert len(item_ids) == len(
        set(item_ids)
    )


def test_order_item_ids_are_contiguous():
    transactions = list(
        generate_transactions(
            start_order_id=1,
            start_order_item_id=100,
            count=100,
            customer_ids=[1, 2, 3, 4, 5],
            store_ids=[1, 2],
            product_prices={
                1: Decimal("100.00"),
                2: Decimal("200.00"),
                3: Decimal("300.00"),
                4: Decimal("400.00"),
                5: Decimal("500.00"),
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
    )

    item_ids = [
        item.order_item_id
        for transaction in transactions
        for item in transaction.items
    ]

    expected_ids = list(
        range(
            100,
            100 + len(item_ids),
        )
    )

    assert item_ids == expected_ids


def test_order_ids_are_unique():
    transactions = list(
        generate_transactions(
            start_order_id=500,
            start_order_item_id=1_000,
            count=100,
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
    )

    order_ids = [
        transaction.order.order_id
        for transaction in transactions
    ]

    assert len(order_ids) == len(
        set(order_ids)
    )

    assert order_ids == list(
        range(500, 600)
    )


def test_transactions_are_deterministic():
    kwargs = {
        "start_order_id": 1,
        "start_order_item_id": 1,
        "count": 100,
        "customer_ids": [1, 2, 3, 4, 5],
        "store_ids": [1, 2],
        "product_prices": {
            1: Decimal("100.00"),
            2: Decimal("200.00"),
            3: Decimal("300.00"),
            4: Decimal("400.00"),
            5: Decimal("500.00"),
        },
        "seed": 42,
        "start_date": datetime(
            2026,
            1,
            1,
        ),
        "end_date": datetime(
            2026,
            12,
            31,
        ),
    }

    first = list(
        generate_transactions(**kwargs)
    )

    second = list(
        generate_transactions(**kwargs)
    )

    assert first == second
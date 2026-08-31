from decimal import Decimal

from retailpulse.generators.order_items import (
    generate_order_items,
)


def test_order_items_have_valid_references():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
        3: Decimal("500.00"),
        4: Decimal("750.00"),
    }

    items = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=3,
        )
    )

    assert len(items) == 3

    assert all(
        item.order_id == 1
        for item in items
    )

    assert all(
        item.product_id in prices
        for item in items
    )


def test_order_item_ids_are_unique():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
        3: Decimal("500.00"),
    }

    items = list(
        generate_order_items(
            order_id=10,
            order_item_start_id=100,
            product_prices=prices,
            seed=42,
            item_count=3,
        )
    )

    ids = [
        item.order_item_id
        for item in items
    ]

    assert len(ids) == len(set(ids))


def test_order_item_financials_are_consistent():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
        3: Decimal("500.00"),
    }

    items = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=3,
        )
    )

    for item in items:
        gross_amount = (
            item.unit_price * item.quantity
        )

        expected_total = (
            gross_amount
            - item.discount_amount
            + item.tax_amount
        ).quantize(
            Decimal("0.01")
        )

        assert item.line_total == expected_total


def test_order_item_quantity_is_positive():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
    }

    items = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=2,
        )
    )

    assert all(
        item.quantity > 0
        for item in items
    )


def test_order_item_prices_are_non_negative():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
    }

    items = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=2,
        )
    )

    assert all(
        item.unit_price >= Decimal("0.00")
        for item in items
    )


def test_order_item_generation_is_deterministic():
    prices = {
        1: Decimal("100.00"),
        2: Decimal("250.00"),
        3: Decimal("500.00"),
    }

    first = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=3,
        )
    )

    second = list(
        generate_order_items(
            order_id=1,
            order_item_start_id=1,
            product_prices=prices,
            seed=42,
            item_count=3,
        )
    )

    assert first == second
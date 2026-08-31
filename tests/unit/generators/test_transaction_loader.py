from decimal import Decimal

import pytest

from retailpulse.generators.order_items import (
    generate_order_items,
)
from retailpulse.generators.orders import (
    generate_order_attributes,
)
from retailpulse.generators.transaction_loader import (
    validate_transaction_batch,
)
from retailpulse.generators.transactions import (
    build_order,
    build_order_transaction,
)


def create_transaction(
    order_id: int,
    order_item_start_id: int,
):
    prices = {
        1: Decimal("100.00"),
        2: Decimal("200.00"),
        3: Decimal("300.00"),
    }

    (
        generated_order_id,
        customer_id,
        store_id,
        order_channel,
        order_status,
        order_date,
        currency_code,
    ) = generate_order_attributes(
        order_id=order_id,
        customer_ids=[1, 2, 3],
        store_ids=[1, 2],
        seed=42 + order_id,
        start_date=__import__(
            "datetime"
        ).datetime(
            2026,
            1,
            1,
        ),
        end_date=__import__(
            "datetime"
        ).datetime(
            2026,
            12,
            31,
        ),
    )

    items = list(
        generate_order_items(
            order_id=generated_order_id,
            order_item_start_id=(
                order_item_start_id
            ),
            product_prices=prices,
            seed=100 + order_id,
            item_count=2,
        )
    )

    order = build_order(
        order_id=generated_order_id,
        customer_id=customer_id,
        store_id=store_id,
        order_channel=order_channel,
        order_status=order_status,
        order_date=order_date,
        currency_code=currency_code,
        items=items,
        shipping_amount=Decimal("50.00"),
    )

    return build_order_transaction(
        order=order,
        items=items,
    )


def test_empty_batch_is_rejected():
    with pytest.raises(ValueError):
        validate_transaction_batch([])


def test_valid_batch_is_accepted():
    transaction = create_transaction(
        order_id=1,
        order_item_start_id=1,
    )

    result = validate_transaction_batch(
        [transaction]
    )

    assert len(result) == 1


def test_duplicate_order_ids_are_rejected():
    transaction_1 = create_transaction(
        order_id=1,
        order_item_start_id=1,
    )

    transaction_2 = create_transaction(
        order_id=1,
        order_item_start_id=3,
    )

    with pytest.raises(ValueError):
        validate_transaction_batch(
            [
                transaction_1,
                transaction_2,
            ]
        )


def test_duplicate_order_item_ids_are_rejected():
    transaction_1 = create_transaction(
        order_id=1,
        order_item_start_id=1,
    )

    transaction_2 = create_transaction(
        order_id=2,
        order_item_start_id=1,
    )

    with pytest.raises(ValueError):
        validate_transaction_batch(
            [
                transaction_1,
                transaction_2,
            ]
        )


def test_wrong_order_reference_is_rejected():
    transaction = create_transaction(
        order_id=1,
        order_item_start_id=1,
    )

    item = transaction.items[0]

    bad_item = type(item)(
        order_item_id=item.order_item_id,
        order_id=999,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=item.unit_price,
        discount_amount=item.discount_amount,
        tax_amount=item.tax_amount,
        line_total=item.line_total,
    )

    bad_transaction = type(transaction)(
        order=transaction.order,
        items=(bad_item,),
    )

    with pytest.raises(ValueError):
        validate_transaction_batch(
            [bad_transaction]
        )
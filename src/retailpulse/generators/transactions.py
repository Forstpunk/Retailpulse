from dataclasses import dataclass
from decimal import Decimal

from retailpulse.generators.order_items import (
    OrderItem,
)
from retailpulse.generators.orders import (
    Order,
)


@dataclass(frozen=True)
class OrderTransaction:
    order: Order
    items: tuple[OrderItem, ...]


def build_order(
    *,
    order_id: int,
    customer_id: int,
    store_id: int | None,
    order_channel: str,
    order_status: str,
    order_date,
    currency_code: str,
    items: list[OrderItem],
    shipping_amount: Decimal,
) -> Order:
    """
    Build a financially reconciled Order from its items.
    """

    if not items:
        raise ValueError(
            "An order must contain at least one item"
        )

    subtotal_amount = sum(
        (
            item.unit_price * item.quantity
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    discount_amount = sum(
        (
            item.discount_amount
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    tax_amount = sum(
        (
            item.tax_amount
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    total_amount = (
        subtotal_amount
        - discount_amount
        + tax_amount
        + shipping_amount
    ).quantize(
        Decimal("0.01")
    )

    if subtotal_amount < Decimal("0.00"):
        raise ValueError(
            "subtotal_amount cannot be negative"
        )

    if discount_amount > subtotal_amount:
        raise ValueError(
            "discount_amount cannot exceed subtotal"
        )

    if tax_amount < Decimal("0.00"):
        raise ValueError(
            "tax_amount cannot be negative"
        )

    if shipping_amount < Decimal("0.00"):
        raise ValueError(
            "shipping_amount cannot be negative"
        )

    if total_amount < Decimal("0.00"):
        raise ValueError(
            "total_amount cannot be negative"
        )

    return Order(
        order_id=order_id,
        customer_id=customer_id,
        store_id=store_id,
        order_channel=order_channel,
        order_status=order_status,
        order_date=order_date,
        currency_code=currency_code,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        total_amount=total_amount,
    )


def build_order_transaction(
    *,
    order: Order,
    items: list[OrderItem],
) -> OrderTransaction:
    """
    Validate and construct a complete order transaction.
    """

    if not items:
        raise ValueError(
            "Order transaction must contain items"
        )

    if any(
        item.order_id != order.order_id
        for item in items
    ):
        raise ValueError(
            "Every order item must reference "
            "the parent order"
        )

    calculated_subtotal = sum(
        (
            item.unit_price * item.quantity
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    calculated_discount = sum(
        (
            item.discount_amount
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    calculated_tax = sum(
        (
            item.tax_amount
            for item in items
        ),
        Decimal("0.00"),
    ).quantize(
        Decimal("0.01")
    )

    expected_total = (
        calculated_subtotal
        - calculated_discount
        + calculated_tax
        + order.shipping_amount
    ).quantize(
        Decimal("0.01")
    )

    if order.subtotal_amount != calculated_subtotal:
        raise ValueError(
            "Order subtotal does not reconcile "
            "with order items"
        )

    if order.discount_amount != calculated_discount:
        raise ValueError(
            "Order discount does not reconcile "
            "with order items"
        )

    if order.tax_amount != calculated_tax:
        raise ValueError(
            "Order tax does not reconcile "
            "with order items"
        )

    if order.total_amount != expected_total:
        raise ValueError(
            "Order total does not reconcile "
            "with order financial components"
        )

    return OrderTransaction(
        order=order,
        items=tuple(items),
    )
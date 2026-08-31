from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from random import Random


@dataclass(frozen=True)
class OrderItem:
    order_item_id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal


def generate_order_items(
    order_id: int,
    order_item_start_id: int,
    product_prices: dict[int, Decimal],
    seed: int,
    item_count: int | None = None,
) -> Iterator[OrderItem]:
    """
    Generate order items for a single order.

    Each generated item references an existing product and
    derives its financial values from the product price.

    Parameters
    ----------
    order_id:
        Existing order ID.

    order_item_start_id:
        First order_item_id assigned to this order.

    product_prices:
        Mapping of product_id to product unit price.

    seed:
        Random seed used for deterministic generation.

    item_count:
        Number of items to generate for the order.
        If omitted, a basket size is selected randomly.

    Yields
    ------
    OrderItem
        Generated order item.
    """

    if order_id <= 0:
        raise ValueError(
            "order_id must be greater than zero"
        )

    if order_item_start_id <= 0:
        raise ValueError(
            "order_item_start_id must be greater than zero"
        )

    if not product_prices:
        raise ValueError(
            "product_prices cannot be empty"
        )

    rng = Random(seed)

    if item_count is None:
        item_count = rng.choices(
            population=[1, 2, 3, 4, 5],
            weights=[0.45, 0.25, 0.15, 0.10, 0.05],
            k=1,
        )[0]

    if item_count <= 0:
        raise ValueError(
            "item_count must be greater than zero"
        )

    available_product_ids = list(
        product_prices.keys()
    )

    actual_item_count = min(
        item_count,
        len(available_product_ids),
    )

    selected_products = rng.sample(
        available_product_ids,
        k=actual_item_count,
    )

    for offset, product_id in enumerate(
        selected_products
    ):
        quantity = rng.choices(
            population=[1, 2, 3, 4],
            weights=[0.60, 0.25, 0.10, 0.05],
            k=1,
        )[0]

        unit_price = product_prices[
            product_id
        ]

        gross_amount = (
            unit_price * quantity
        ).quantize(
            Decimal("0.01")
        )

        discount_rate = rng.choices(
            population=[
                Decimal("0.00"),
                Decimal("0.05"),
                Decimal("0.10"),
                Decimal("0.15"),
            ],
            weights=[0.70, 0.15, 0.10, 0.05],
            k=1,
        )[0]

        discount_amount = (
            gross_amount * discount_rate
        ).quantize(
            Decimal("0.01")
        )

        taxable_amount = (
            gross_amount - discount_amount
        ).quantize(
            Decimal("0.01")
        )

        tax_amount = (
            taxable_amount * Decimal("0.18")
        ).quantize(
            Decimal("0.01")
        )

        line_total = (
            taxable_amount + tax_amount
        ).quantize(
            Decimal("0.01")
        )

        yield OrderItem(
            order_item_id=(
                order_item_start_id + offset
            ),
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            line_total=line_total,
        )
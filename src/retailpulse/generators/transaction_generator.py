from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from random import Random

from retailpulse.generators.order_items import (
    generate_order_items,
)
from retailpulse.generators.orders import (
    generate_order_attributes,
)
from retailpulse.generators.transactions import (
    OrderTransaction,
    build_order,
    build_order_transaction,
)


def generate_transactions(
    *,
    start_order_id: int,
    start_order_item_id: int,
    count: int,
    customer_ids: list[int],
    store_ids: list[int],
    product_prices: dict[int, Decimal],
    seed: int,
    start_date: datetime,
    end_date: datetime,
) -> Iterator[OrderTransaction]:
    """
    Generate complete, financially reconciled transactions.

    Order IDs and order-item IDs are globally unique within
    the generated sequence.

    The generator is lazy, so transactions are produced one
    at a time rather than materializing the complete dataset
    in memory.
    """

    if start_order_id <= 0:
        raise ValueError(
            "start_order_id must be greater than zero"
        )

    if start_order_item_id <= 0:
        raise ValueError(
            "start_order_item_id must be greater than zero"
        )

    if count < 0:
        raise ValueError(
            "count cannot be negative"
        )

    if not customer_ids:
        raise ValueError(
            "customer_ids cannot be empty"
        )

    if not store_ids:
        raise ValueError(
            "store_ids cannot be empty"
        )

    if not product_prices:
        raise ValueError(
            "product_prices cannot be empty"
        )

    next_order_item_id = start_order_item_id

    for offset in range(count):
        order_id = (
            start_order_id + offset
        )

        # Use independent deterministic seeds for
        # order-level and item-level randomness.
        order_seed = (
            seed
            + (order_id * 2)
        )

        item_seed = (
            seed
            + (order_id * 2)
            + 1
        )

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
            customer_ids=customer_ids,
            store_ids=store_ids,
            seed=order_seed,
            start_date=start_date,
            end_date=end_date,
        )

        item_rng = Random(item_seed)

        item_count = item_rng.choices(
            population=[1, 2, 3, 4, 5],
            weights=[
                0.45,
                0.25,
                0.15,
                0.10,
                0.05,
            ],
            k=1,
        )[0]

        items = list(
            generate_order_items(
                order_id=generated_order_id,
                order_item_start_id=(
                    next_order_item_id
                ),
                product_prices=product_prices,
                seed=item_seed,
                item_count=item_count,
            )
        )

        # Advance the global item ID allocator.
        next_order_item_id += len(items)

        if order_channel == "STORE":
            shipping_amount = Decimal("0.00")
        else:
            shipping_amount = Decimal("50.00")

        order = build_order(
            order_id=generated_order_id,
            customer_id=customer_id,
            store_id=store_id,
            order_channel=order_channel,
            order_status=order_status,
            order_date=order_date,
            currency_code=currency_code,
            items=items,
            shipping_amount=shipping_amount,
        )

        yield build_order_transaction(
            order=order,
            items=items,
        )
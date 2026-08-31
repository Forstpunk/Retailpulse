from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal

from retailpulse.generators.transaction_generator import (
    generate_transactions,
)
from retailpulse.generators.transactions import (
    OrderTransaction,
)


def calculate_order_item_offset(
    *,
    start_order_id: int,
    start_order_item_id: int,
    start_offset: int,
    customer_ids: list[int],
    store_ids: list[int],
    product_prices: dict[int, Decimal],
    seed: int,
    start_date: datetime,
    end_date: datetime,
) -> int:
    """
    Calculate the order_item_id required to resume
    generation at a specific order offset.

    The existing transaction generator assigns
    order_item IDs sequentially, so we reproduce the
    preceding transactions to determine how many
    order items were consumed.
    """

    if start_offset < 0:
        raise ValueError(
            "start_offset cannot be negative"
        )

    if start_offset == 0:
        return start_order_item_id

    preceding_transactions = (
        generate_transactions(
            start_order_id=start_order_id,
            start_order_item_id=start_order_item_id,
            count=start_offset,
            customer_ids=customer_ids,
            store_ids=store_ids,
            product_prices=product_prices,
            seed=seed,
            start_date=start_date,
            end_date=end_date,
        )
    )

    next_order_item_id = (
        start_order_item_id
    )

    for transaction in preceding_transactions:
        next_order_item_id += len(
            transaction.items
        )

    return next_order_item_id


def generate_transaction_slice(
    *,
    start_order_id: int,
    start_order_item_id: int,
    start_offset: int,
    count: int,
    customer_ids: list[int],
    store_ids: list[int],
    product_prices: dict[int, Decimal],
    seed: int,
    start_date: datetime,
    end_date: datetime,
) -> Iterator[OrderTransaction]:
    """
    Generate a deterministic slice of the complete
    transaction stream.

    start_offset identifies the first order to generate.
    """

    if start_offset < 0:
        raise ValueError(
            "start_offset cannot be negative"
        )

    if count < 0:
        raise ValueError(
            "count cannot be negative"
        )

    if count == 0:
        return

    resume_order_id = (
        start_order_id
        + start_offset
    )

    resume_order_item_id = (
        calculate_order_item_offset(
            start_order_id=start_order_id,
            start_order_item_id=start_order_item_id,
            start_offset=start_offset,
            customer_ids=customer_ids,
            store_ids=store_ids,
            product_prices=product_prices,
            seed=seed,
            start_date=start_date,
            end_date=end_date,
        )
    )

    yield from generate_transactions(
        start_order_id=resume_order_id,
        start_order_item_id=resume_order_item_id,
        count=count,
        customer_ids=customer_ids,
        store_ids=store_ids,
        product_prices=product_prices,
        seed=seed,
        start_date=start_date,
        end_date=end_date,
    )
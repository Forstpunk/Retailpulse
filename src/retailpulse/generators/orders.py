from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from random import Random


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    store_id: int | None
    order_channel: str
    order_status: str
    order_date: datetime
    currency_code: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal


ORDER_CHANNELS = [
    "STORE",
    "WEB",
    "MOBILE",
    "MARKETPLACE",
]


ORDER_CHANNEL_WEIGHTS = [
    0.40,
    0.30,
    0.15,
    0.15,
]


ORDER_STATUSES = [
    "CREATED",
    "CONFIRMED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    "RETURNED",
]


ORDER_STATUS_WEIGHTS = [
    0.03,
    0.07,
    0.08,
    0.12,
    0.62,
    0.06,
    0.02,
]


def generate_order_attributes(
    order_id: int,
    customer_ids: list[int],
    store_ids: list[int],
    seed: int,
    start_date: datetime,
    end_date: datetime,
) -> tuple[
    int,
    int,
    int | None,
    str,
    str,
    datetime,
    str,
]:
    """
    Generate the non-financial attributes of one order.

    Financial fields are calculated after order items
    have been generated.
    """

    if order_id <= 0:
        raise ValueError(
            "order_id must be greater than zero"
        )

    if not customer_ids:
        raise ValueError(
            "customer_ids cannot be empty"
        )

    if not store_ids:
        raise ValueError(
            "store_ids cannot be empty"
        )

    if end_date < start_date:
        raise ValueError(
            "end_date cannot be before start_date"
        )

    rng = Random(seed)

    total_seconds = int(
        (
            end_date - start_date
        ).total_seconds()
    )

    customer_id = rng.choice(
        customer_ids
    )

    store_id = rng.choice(
        store_ids
    )

    order_channel = rng.choices(
        ORDER_CHANNELS,
        weights=ORDER_CHANNEL_WEIGHTS,
        k=1,
    )[0]

    order_status = rng.choices(
        ORDER_STATUSES,
        weights=ORDER_STATUS_WEIGHTS,
        k=1,
    )[0]

    order_date = (
        start_date
        + timedelta(
            seconds=rng.randint(
                0,
                total_seconds,
            )
        )
    )

    return (
        order_id,
        customer_id,
        store_id,
        order_channel,
        order_status,
        order_date,
        "INR",
    )


def generate_orders(
    count: int,
    customer_ids: list[int],
    store_ids: list[int],
    seed: int,
    start_date: datetime,
    end_date: datetime,
) -> Iterator[tuple]:
    """
    Generate order attributes lazily.
    """

    if count < 0:
        raise ValueError(
            "count cannot be negative"
        )

    for order_id in range(
        1,
        count + 1,
    ):
        yield generate_order_attributes(
            order_id=order_id,
            customer_ids=customer_ids,
            store_ids=store_ids,
            seed=seed + order_id,
            start_date=start_date,
            end_date=end_date,
        )
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest

from retailpulse.common.database import get_connection
from retailpulse.generators.order_items import OrderItem
from retailpulse.generators.transaction_loader import (
    load_transaction_batch,
)
from retailpulse.generators.transactions import (
    OrderTransaction,
    build_order,
)


def make_invalid_transaction() -> OrderTransaction:
    """
    Create a transaction that passes the Python-level
    transaction model but violates the database FK.

    customer_id=999_999_999 is intentionally invalid.
    """

    item = OrderItem(
        order_item_id=900_000_001,
        order_id=900_000_001,
        product_id=1,
        quantity=1,
        unit_price=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("18.00"),
        line_total=Decimal("118.00"),
    )

    order = build_order(
        order_id=900_000_001,
        customer_id=999_999_999,
        store_id=1,
        order_channel="WEB",
        order_status="CREATED",
        order_date=datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=UTC,
        ),
        currency_code="INR",
        items=[item],
        shipping_amount=Decimal("0.00"),
    )

    return OrderTransaction(
        order=order,
        items=(item,),
    )


def test_failed_transaction_batch_rolls_back() -> None:
    transaction = make_invalid_transaction()

    with get_connection() as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM retail.orders
                """
            )

            before = cursor.fetchone()[0]

        with pytest.raises(psycopg.Error):
            load_transaction_batch(
                connection,
                [transaction],
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM retail.orders
                """
            )

            after = cursor.fetchone()[0]

    assert after == before
from collections.abc import Iterable

from psycopg import Connection

from retailpulse.generators.transactions import (
    OrderTransaction,
)


def validate_transaction_batch(
    transactions: Iterable[OrderTransaction],
) -> list[OrderTransaction]:
    """
    Materialize and validate a transaction batch before
    sending anything to PostgreSQL.
    """

    batch = list(transactions)

    if not batch:
        raise ValueError(
            "Transaction batch cannot be empty"
        )

    order_ids: set[int] = set()
    order_item_ids: set[int] = set()

    for transaction in batch:
        order = transaction.order

        if order.order_id in order_ids:
            raise ValueError(
                f"Duplicate order_id: "
                f"{order.order_id}"
            )

        order_ids.add(order.order_id)

        if not transaction.items:
            raise ValueError(
                f"Order {order.order_id} "
                "has no order items"
            )

        for item in transaction.items:

            if item.order_id != order.order_id:
                raise ValueError(
                    "Order item references "
                    "the wrong order"
                )

            if item.order_item_id in order_item_ids:
                raise ValueError(
                    f"Duplicate order_item_id: "
                    f"{item.order_item_id}"
                )

            order_item_ids.add(
                item.order_item_id
            )

    return batch


def load_transaction_batch(
    connection: Connection,
    transactions: Iterable[OrderTransaction],
) -> tuple[int, int]:
    """
    Validate and atomically load one physical
    transaction batch.

    This function owns the transaction boundary.

    If either the orders or order_items COPY operation
    fails, the entire database load is rolled back.
    """

    batch = validate_transaction_batch(
        transactions
    )

    orders = [
        transaction.order
        for transaction in batch
    ]

    order_items = [
        item
        for transaction in batch
        for item in transaction.items
    ]

    with connection.transaction():

        _copy_orders(
            connection,
            orders,
        )

        _copy_order_items(
            connection,
            order_items,
        )

    return (
        len(orders),
        len(order_items),
    )


def _copy_orders(
    connection: Connection,
    orders: list,
) -> None:
    """
    COPY orders into PostgreSQL.

    This function does not create or commit a transaction.
    The caller owns the transaction boundary.
    """

    with connection.cursor() as cursor, cursor.copy(
        """
            COPY retail.orders (
                order_id,
                customer_id,
                store_id,
                order_channel,
                order_status,
                order_date,
                currency_code,
                subtotal_amount,
                discount_amount,
                tax_amount,
                shipping_amount,
                total_amount
            )
            FROM STDIN
            """
    ) as copy:

        for order in orders:

            copy.write_row(
                (
                    order.order_id,
                    order.customer_id,
                    order.store_id,
                    order.order_channel,
                    order.order_status,
                    order.order_date,
                    order.currency_code,
                    order.subtotal_amount,
                    order.discount_amount,
                    order.tax_amount,
                    order.shipping_amount,
                    order.total_amount,
                )
            )


def _copy_order_items(
    connection: Connection,
    order_items: list,
) -> None:
    """
    COPY order items into PostgreSQL.

    This function does not create or commit a transaction.
    The caller owns the transaction boundary.
    """

    with connection.cursor() as cursor, cursor.copy(
        """
            COPY retail.order_items (
                order_item_id,
                order_id,
                product_id,
                quantity,
                unit_price,
                discount_amount,
                tax_amount,
                line_total
            )
            FROM STDIN
            """
    ) as copy:

        for item in order_items:

            copy.write_row(
                (
                    item.order_item_id,
                    item.order_id,
                    item.product_id,
                    item.quantity,
                    item.unit_price,
                    item.discount_amount,
                    item.tax_amount,
                    item.line_total,
                )
            )
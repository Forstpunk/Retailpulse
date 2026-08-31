from decimal import Decimal

from psycopg import Connection


def get_customer_ids(
    connection: Connection,
) -> list[int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT customer_id
            FROM retail.customers
            WHERE status = 'ACTIVE'
            ORDER BY customer_id
            """
        )

        rows = cursor.fetchall()

    return [
        int(row[0])
        for row in rows
    ]


def get_store_ids(
    connection: Connection,
) -> list[int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT store_id
            FROM retail.stores
            WHERE status = 'OPEN'
            ORDER BY store_id
            """
        )

        rows = cursor.fetchall()

    return [
        int(row[0])
        for row in rows
    ]

def get_product_prices(
    connection: Connection,
) -> dict[int, Decimal]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                product_id,
                unit_price
            FROM retail.products
            WHERE status = 'ACTIVE'
            ORDER BY product_id
            """
        )

        rows = cursor.fetchall()

    return {
        int(product_id): Decimal(unit_price)
        for product_id, unit_price in rows
    }


def get_next_order_id(
    connection: Connection,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(
                MAX(order_id),
                0
            ) + 1
            FROM retail.orders
            """
        )

        result = cursor.fetchone()

    if result is None:
        raise RuntimeError(
            "Failed to determine next order_id"
        )

    return int(result[0])


def get_next_order_item_id(
    connection: Connection,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(
                MAX(order_item_id),
                0
            ) + 1
            FROM retail.order_items
            """
        )

        result = cursor.fetchone()

    if result is None:
        raise RuntimeError(
            "Failed to determine next order_item_id"
        )

    return int(result[0])
from psycopg import Connection

from retailpulse.analytics.models.fact_order_item import (
    SourceOrderItem,
)


def get_order_items(
    connection: Connection,
    *,
    since_order_item_id: int = 0,
) -> list[SourceOrderItem]:
    """
    Read order items from the retail source schema.

    since_order_item_id restricts the read to items with
    order_item_id greater than the given value — see
    order_repository.get_orders for why an id column is
    used as the watermark rather than a timestamp.

    This repository is read-only.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                order_item_id,
                order_id,
                product_id,
                quantity,
                unit_price,
                discount_amount,
                tax_amount,
                line_total,
                created_at,
                updated_at
            FROM retail.order_items
            WHERE order_item_id > %s
            ORDER BY order_item_id
            """,
            (since_order_item_id,),
        )

        rows = cursor.fetchall()

    return [
        SourceOrderItem(
            order_item_id=row[0],
            order_id=row[1],
            product_id=row[2],
            quantity=row[3],
            unit_price=row[4],
            discount_amount=row[5],
            tax_amount=row[6],
            line_total=row[7],
            created_at=row[8],
            updated_at=row[9],
        )
        for row in rows
    ]
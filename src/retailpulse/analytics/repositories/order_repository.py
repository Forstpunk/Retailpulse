from psycopg import Connection

from retailpulse.analytics.models.fact_order import (
    SourceOrder,
)


def get_orders(
    connection: Connection,
    *,
    since_order_id: int = 0,
) -> list[SourceOrder]:
    """
    Read orders from the retail source schema.

    since_order_id restricts the read to orders with
    order_id greater than the given value — the
    incremental-processing watermark for this source is
    order_id, which is monotonically assigned and immune
    to clock-skew issues a timestamp watermark would have.

    This repository is read-only.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
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
                total_amount,
                created_at,
                updated_at
            FROM retail.orders
            WHERE order_id > %s
            ORDER BY order_id
            """,
            (since_order_id,),
        )

        rows = cursor.fetchall()

    return [
        SourceOrder(
            order_id=row[0],
            customer_id=row[1],
            store_id=row[2],
            order_channel=row[3],
            order_status=row[4],
            order_date=row[5],
            currency_code=row[6],
            subtotal_amount=row[7],
            discount_amount=row[8],
            tax_amount=row[9],
            shipping_amount=row[10],
            total_amount=row[11],
            created_at=row[12],
            updated_at=row[13],
        )
        for row in rows
    ]
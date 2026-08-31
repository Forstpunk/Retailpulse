from psycopg import Connection

from retailpulse.analytics.models.product import (
    SourceProduct,
)


def get_products(
    connection: Connection,
) -> list[SourceProduct]:
    """
    Read products from the retail source schema.

    This repository is read-only.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                product_id,
                sku,
                product_name,
                category_id,
                supplier_id,
                unit_price,
                cost_price,
                status,
                created_at,
                updated_at
            FROM retail.products
            ORDER BY product_id
            """
        )

        rows = cursor.fetchall()

    return [
        SourceProduct(
            product_id=row[0],
            sku=row[1],
            product_name=row[2],
            category_id=row[3],
            supplier_id=row[4],
            unit_price=row[5],
            cost_price=row[6],
            status=row[7],
            created_at=row[8],
            updated_at=row[9],
        )
        for row in rows
    ]
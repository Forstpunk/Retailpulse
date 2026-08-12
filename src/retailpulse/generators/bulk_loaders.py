from collections.abc import Iterable

from psycopg import Connection


def copy_products(
    connection: Connection,
    products: Iterable,
) -> None:
    with connection.cursor() as cursor:
        with cursor.copy(
            """
            COPY retail.products (
                product_id,
                sku,
                product_name,
                category_id,
                supplier_id,
                unit_price,
                cost_price,
                status
            )
            FROM STDIN
            """
        ) as copy:
            for product in products:
                copy.write_row(
                    (
                        product.product_id,
                        product.sku,
                        product.product_name,
                        product.category_id,
                        product.supplier_id,
                        product.unit_price,
                        product.cost_price,
                        product.status,
                    )
                )
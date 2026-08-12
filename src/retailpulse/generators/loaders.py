from collections.abc import Iterable

from psycopg import Connection


def insert_categories(
    connection: Connection,
    categories: Iterable,
) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO retail.categories (
                category_id,
                category_name,
                parent_category_id
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (category_id) DO NOTHING
            """,
            [
                (
                    category.category_id,
                    category.category_name,
                    category.parent_category_id,
                )
                for category in categories
            ],
        )


def insert_suppliers(
    connection: Connection,
    suppliers: Iterable,
) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO retail.suppliers (
                supplier_id,
                supplier_name,
                country_code,
                status
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (supplier_id) DO NOTHING
            """,
            [
                (
                    supplier.supplier_id,
                    supplier.supplier_name,
                    supplier.country_code,
                    supplier.status,
                )
                for supplier in suppliers
            ],
        )


def insert_stores(
    connection: Connection,
    stores: Iterable,
) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO retail.stores (
                store_id,
                store_code,
                store_name,
                city,
                state,
                country_code,
                region,
                store_type,
                opened_date,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (store_id) DO NOTHING
            """,
            [
                (
                    store.store_id,
                    store.store_code,
                    store.store_name,
                    store.city,
                    store.state,
                    store.country_code,
                    store.region,
                    store.store_type,
                    store.opened_date,
                    store.status,
                )
                for store in stores
            ],
        )
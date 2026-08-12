from psycopg import Connection


def assert_reference_counts(
    connection: Connection,
    *,
    expected_categories: int,
    expected_suppliers: int,
    expected_stores: int,
    expected_products: int,
) -> None:
    checks = {
        "categories": expected_categories,
        "suppliers": expected_suppliers,
        "stores": expected_stores,
        "products": expected_products,
    }

    with connection.cursor() as cursor:
        for table_name, expected_count in checks.items():
            cursor.execute(
                f"SELECT COUNT(*) FROM retail.{table_name}"
            )

            actual_count = cursor.fetchone()[0]

            if actual_count != expected_count:
                raise AssertionError(
                    f"{table_name}: expected "
                    f"{expected_count}, got {actual_count}"
                )
from psycopg import Connection

from retailpulse.generators.config import (
    GeneratorConfig,
)


def reference_data_is_ready(
    connection: Connection,
    config: GeneratorConfig,
) -> bool:
    """
    Determine whether the source-system reference data
    has been initialized to the configured minimum size.

    This intentionally checks counts rather than merely
    checking whether tables contain at least one row.
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*)
                 FROM retail.categories),

                (SELECT COUNT(*)
                 FROM retail.suppliers),

                (SELECT COUNT(*)
                 FROM retail.stores),

                (SELECT COUNT(*)
                 FROM retail.products),

                (SELECT COUNT(*)
                 FROM retail.customers)
            """
        )

        row = cursor.fetchone()
        assert row is not None

        (
            categories,
            suppliers,
            stores,
            products,
            customers,
        ) = row

    return (
        categories >= config.categories
        and suppliers >= config.suppliers
        and stores >= config.stores
        and products >= config.products
        and customers >= config.customers
    )
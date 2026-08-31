from psycopg import Connection

from retailpulse.generators.batching import (
    batched,
)
from retailpulse.generators.bulk_loaders import (
    copy_customers,
    copy_products,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.generators.customers import (
    generate_customers,
)
from retailpulse.generators.loaders import (
    insert_categories,
    insert_stores,
    insert_suppliers,
)
from retailpulse.generators.products import (
    generate_products,
)
from retailpulse.generators.reference import (
    generate_categories,
    generate_stores,
    generate_suppliers,
)


def bootstrap_reference_data(
    connection: Connection,
    config: GeneratorConfig,
) -> dict[str, int]:
    """
    Generate and load the source-system reference data.

    This operation is intended for initial source-system
    bootstrap rather than transaction retries.
    """

    print()
    print(
        "Generating reference data..."
    )

    # =========================================================
    # Generate reference entities
    # =========================================================

    categories = generate_categories()

    suppliers = generate_suppliers(
        config.suppliers,
    )

    stores = generate_stores(
        config.stores,
    )

    print(
        f"Generated categories: "
        f"{len(categories):,}"
    )

    print(
        f"Generated suppliers: "
        f"{len(suppliers):,}"
    )

    print(
        f"Generated stores: "
        f"{len(stores):,}"
    )

    category_ids = [
        category.category_id
        for category in categories
    ]

    supplier_ids = [
        supplier.supplier_id
        for supplier in suppliers
    ]

    # =========================================================
    # Load reference tables
    # =========================================================

    print()
    print(
        "Loading categories..."
    )

    insert_categories(
        connection,
        categories,
    )

    print(
        "Loading suppliers..."
    )

    insert_suppliers(
        connection,
        suppliers,
    )

    print(
        "Loading stores..."
    )

    insert_stores(
        connection,
        stores,
    )

    # =========================================================
    # Products
    # =========================================================

    print()
    print(
        "Generating products..."
    )

    product_generator = generate_products(
        count=config.products,
        category_ids=category_ids,
        supplier_ids=supplier_ids,
        seed=config.seed,
    )

    products_loaded = 0

    for product_batch in batched(
        product_generator,
        config.batch_size,
    ):
        current_batch_size = len(
            product_batch,
        )

        print(
            "Bulk loading product batch: "
            f"{current_batch_size:,}"
        )

        copy_products(
            connection,
            product_batch,
        )

        products_loaded += current_batch_size

    if products_loaded != config.products:
        raise RuntimeError(
            "Product load count does not "
            "match configured count: "
            f"expected={config.products}, "
            f"actual={products_loaded}"
        )

    # =========================================================
    # Customers
    # =========================================================

    print()
    print(
        "Generating customers..."
    )

    customer_generator = generate_customers(
        count=config.customers,
        seed=config.seed,
    )

    customers_loaded = 0

    for customer_batch in batched(
        customer_generator,
        config.batch_size,
    ):
        current_batch_size = len(
            customer_batch,
        )

        print(
            "Bulk loading customer batch: "
            f"{current_batch_size:,}"
        )

        copy_customers(
            connection,
            customer_batch,
        )

        customers_loaded += current_batch_size

    if customers_loaded != config.customers:
        raise RuntimeError(
            "Customer load count does not "
            "match configured count: "
            f"expected={config.customers}, "
            f"actual={customers_loaded}"
        )

    return {
        "categories": len(categories),
        "suppliers": len(suppliers),
        "stores": len(stores),
        "products": products_loaded,
        "customers": customers_loaded,
    }
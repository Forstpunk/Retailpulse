from retailpulse.common.database import get_connection
from retailpulse.generators.bulk_loaders import copy_products
from retailpulse.generators.config import DEV_CONFIG
from retailpulse.generators.products import generate_products
from retailpulse.generators.loaders import (
    insert_categories,
    insert_stores,
    insert_suppliers,
)
from retailpulse.generators.reference import (
    generate_categories,
    generate_stores,
    generate_suppliers,
)


def main() -> None:
    config = DEV_CONFIG

    print("Generating reference data...")

    categories = generate_categories()
    suppliers = generate_suppliers(config.suppliers)
    stores = generate_stores(config.stores)

    category_ids = [
        category.category_id
        for category in categories
    ]

    supplier_ids = [
        supplier.supplier_id
        for supplier in suppliers
    ]

    products = generate_products(
        count=config.products,
        category_ids=category_ids,
        supplier_ids=supplier_ids,
        seed=config.seed,
    )

    print(f"Generated categories: {len(categories)}")
    print(f"Generated suppliers: {len(suppliers)}")
    print(f"Generated stores: {len(stores)}")
    print(f"Generated products: {len(products)}")

    with get_connection() as connection:
        print("Loading categories...")
        insert_categories(connection, categories)

        print("Loading suppliers...")
        insert_suppliers(connection, suppliers)

        print("Loading stores...")
        insert_stores(connection, stores)

        print("Bulk loading products...")
        copy_products(connection, products)

    print("Transaction committed.")

    print(f"Categories: {len(categories)}")
    print(f"Suppliers: {len(suppliers)}")
    print(f"Stores: {len(stores)}")
    print(f"Products: {len(products)}")


if __name__ == "__main__":
    main()
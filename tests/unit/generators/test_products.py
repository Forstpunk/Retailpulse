from decimal import Decimal

from retailpulse.generators.products import (
    generate_products,
)

CATEGORY_IDS = list(range(1, 11))
SUPPLIER_IDS = list(range(1, 101))


def test_products_have_expected_count():
    products = list(
        generate_products(
            count=100,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    assert len(products) == 100


def test_product_ids_are_unique():
    products = list(
        generate_products(
            count=1_000,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    product_ids = [
        product.product_id
        for product in products
    ]

    assert len(product_ids) == len(
        set(product_ids)
    )


def test_skus_are_unique():
    products = list(
        generate_products(
            count=1_000,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    skus = [
        product.sku
        for product in products
    ]

    assert len(skus) == len(set(skus))


def test_product_references_are_valid():
    products = list(
        generate_products(
            count=1_000,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    assert all(
        product.category_id in CATEGORY_IDS
        for product in products
    )

    assert all(
        product.supplier_id in SUPPLIER_IDS
        for product in products
    )


def test_product_prices_are_non_negative():
    products = list(
        generate_products(
            count=1_000,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    assert all(
        product.unit_price
        >= Decimal("0.00")
        for product in products
    )

    assert all(
        product.cost_price
        >= Decimal("0.00")
        for product in products
    )


def test_product_status_is_valid():
    products = list(
        generate_products(
            count=1_000,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    valid_statuses = {
        "ACTIVE",
        "INACTIVE",
        "DISCONTINUED",
    }

    assert all(
        product.status in valid_statuses
        for product in products
    )


def test_generation_is_deterministic():
    first = list(
        generate_products(
            count=100,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    second = list(
        generate_products(
            count=100,
            category_ids=CATEGORY_IDS,
            supplier_ids=SUPPLIER_IDS,
            seed=42,
        )
    )

    assert first == second
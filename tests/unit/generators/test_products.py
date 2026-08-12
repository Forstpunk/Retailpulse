from retailpulse.generators.products import generate_products


CATEGORY_IDS = list(range(1, 11))
SUPPLIER_IDS = list(range(1, 101))


def test_products_have_expected_count():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    assert len(products) == 100


def test_product_ids_are_unique():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    ids = [product.product_id for product in products]

    assert len(ids) == len(set(ids))


def test_product_skus_are_unique():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    skus = [product.sku for product in products]

    assert len(skus) == len(set(skus))


def test_products_reference_valid_categories():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    assert all(
        product.category_id in CATEGORY_IDS
        for product in products
    )


def test_products_reference_valid_suppliers():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    assert all(
        product.supplier_id in SUPPLIER_IDS
        for product in products
    )


def test_product_price_is_above_cost():
    products = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    assert all(
        product.unit_price > product.cost_price
        for product in products
    )


def test_generation_is_deterministic():
    first = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    second = generate_products(
        count=100,
        category_ids=CATEGORY_IDS,
        supplier_ids=SUPPLIER_IDS,
        seed=42,
    )

    assert first == second
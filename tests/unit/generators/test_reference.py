from retailpulse.generators.reference import (
    generate_categories,
    generate_stores,
    generate_suppliers,
)


def test_categories_have_unique_ids():
    categories = generate_categories()

    ids = [category.category_id for category in categories]

    assert len(ids) == len(set(ids))


def test_categories_have_expected_count():
    categories = generate_categories()

    assert len(categories) == 10


def test_suppliers_have_expected_count():
    suppliers = generate_suppliers(100)

    assert len(suppliers) == 100


def test_suppliers_have_unique_ids():
    suppliers = generate_suppliers(100)

    ids = [supplier.supplier_id for supplier in suppliers]

    assert len(ids) == len(set(ids))


def test_supplier_country_codes_are_valid():
    suppliers = generate_suppliers(100)

    valid_countries = {
        "US",
        "IN",
        "CN",
        "DE",
        "JP",
        "KR",
        "GB",
        "FR",
    }

    assert all(
        supplier.country_code in valid_countries
        for supplier in suppliers
    )


def test_stores_have_expected_count():
    stores = generate_stores(20)

    assert len(stores) == 20


def test_stores_have_unique_ids():
    stores = generate_stores(20)

    ids = [store.store_id for store in stores]

    assert len(ids) == len(set(ids))


def test_stores_have_unique_codes():
    stores = generate_stores(20)

    codes = [store.store_code for store in stores]

    assert len(codes) == len(set(codes))


def test_stores_are_open():
    stores = generate_stores(20)

    assert all(store.status == "OPEN" for store in stores)
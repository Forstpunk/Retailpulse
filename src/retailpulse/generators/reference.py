from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    category_id: int
    category_name: str
    parent_category_id: int | None


@dataclass(frozen=True)
class Supplier:
    supplier_id: int
    supplier_name: str
    country_code: str
    status: str


@dataclass(frozen=True)
class Store:
    store_id: int
    store_code: str
    store_name: str
    city: str
    state: str
    country_code: str
    region: str
    store_type: str
    opened_date: str
    status: str


ROOT_CATEGORIES = [
    "Electronics",
    "Home",
    "Grocery",
    "Clothing",
    "Beauty",
    "Sports",
    "Toys",
    "Automotive",
    "Books",
    "Pet Supplies",
]


SUPPLIER_COUNTRIES = [
    "US",
    "IN",
    "CN",
    "DE",
    "JP",
    "KR",
    "GB",
    "FR",
]


STORE_LOCATIONS = [
    ("Bengaluru", "Karnataka", "IN", "South"),
    ("Mumbai", "Maharashtra", "IN", "West"),
    ("Delhi", "Delhi", "IN", "North"),
    ("Hyderabad", "Telangana", "IN", "South"),
    ("Chennai", "Tamil Nadu", "IN", "South"),
    ("Pune", "Maharashtra", "IN", "West"),
    ("Kolkata", "West Bengal", "IN", "East"),
    ("Ahmedabad", "Gujarat", "IN", "West"),
]


def generate_categories() -> list[Category]:
    return [
        Category(
            category_id=index,
            category_name=name,
            parent_category_id=None,
        )
        for index, name in enumerate(ROOT_CATEGORIES, start=1)
    ]


def generate_suppliers(count: int) -> list[Supplier]:
    return [
        Supplier(
            supplier_id=index,
            supplier_name=f"Supplier {index:05d}",
            country_code=SUPPLIER_COUNTRIES[
                (index - 1) % len(SUPPLIER_COUNTRIES)
            ],
            status="ACTIVE",
        )
        for index in range(1, count + 1)
    ]


def generate_stores(count: int) -> list[Store]:
    stores: list[Store] = []

    for index in range(1, count + 1):
        city, state, country, region = STORE_LOCATIONS[
            (index - 1) % len(STORE_LOCATIONS)
        ]

        stores.append(
            Store(
                store_id=index,
                store_code=f"STR-{index:05d}",
                store_name=f"RetailPulse {city} {index}",
                city=city,
                state=state,
                country_code=country,
                region=region,
                store_type="RETAIL",
                opened_date="2020-01-01",
                status="OPEN",
            )
        )

    return stores
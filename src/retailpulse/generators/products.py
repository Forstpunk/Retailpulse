from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from random import Random


@dataclass(frozen=True)
class Product:
    product_id: int
    sku: str
    product_name: str
    category_id: int
    supplier_id: int
    unit_price: Decimal
    cost_price: Decimal
    status: str


PRODUCT_ADJECTIVES = [
    "Premium",
    "Classic",
    "Organic",
    "Fresh",
    "Smart",
    "Essential",
    "Professional",
    "Advanced",
    "Eco",
    "Daily",
]


PRODUCT_NAMES = [
    "Coffee",
    "Tea",
    "Rice",
    "Flour",
    "Oil",
    "Soap",
    "Shampoo",
    "Detergent",
    "Biscuits",
    "Chocolate",
    "Juice",
    "Cereal",
    "Pasta",
    "Sauce",
    "Snacks",
]

PRODUCT_STATUSES = [
    "ACTIVE",
    "INACTIVE",
    "DISCONTINUED",
]


STATUS_WEIGHTS = [
    0.94,
    0.04,
    0.02,
]


def generate_products(
    count: int,
    category_ids: list[int],
    supplier_ids: list[int],
    seed: int,
) -> Iterator[Product]:
    """
    Generate deterministic synthetic products lazily.

    Products are generated one at a time so that the complete
    product dataset does not have to reside in memory.

    Parameters
    ----------
    count:
        Number of products to generate.

    category_ids:
        Existing category IDs that generated products can reference.

    supplier_ids:
        Existing supplier IDs that generated products can reference.

    seed:
        Seed used to make generation deterministic.

    Yields
    ------
    Product
        A generated product record.
    """

    if count < 0:
        raise ValueError("count cannot be negative")

    if not category_ids:
        raise ValueError(
            "category_ids cannot be empty"
        )

    if not supplier_ids:
        raise ValueError(
            "supplier_ids cannot be empty"
        )

    rng = Random(seed)

    for product_id in range(1, count + 1):
        adjective = rng.choice(
            PRODUCT_ADJECTIVES
        )

        product_type = rng.choice(
            PRODUCT_NAMES
        )

        product_name = (
            f"{adjective} {product_type}"
        )

        category_id = rng.choice(
            category_ids
        )

        supplier_id = rng.choice(
            supplier_ids
        )

        cost_price = Decimal(
            rng.randint(100, 10_000)
        ) / Decimal(100)

        markup = Decimal(
            rng.randint(110, 180)
        ) / Decimal(100)

        unit_price = (
            cost_price * markup
        ).quantize(
            Decimal("0.01")
        )

        status = rng.choices(
            PRODUCT_STATUSES,
            weights=STATUS_WEIGHTS,
            k=1,
        )[0]

        yield Product(
            product_id=product_id,
            sku=f"SKU-{product_id:08d}",
            product_name=product_name,
            category_id=category_id,
            supplier_id=supplier_id,
            unit_price=unit_price,
            cost_price=cost_price,
            status=status,
        )
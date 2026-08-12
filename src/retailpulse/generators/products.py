from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class Product:
    product_id: int
    sku: str
    product_name: str
    category_id: int
    supplier_id: int
    unit_price: float
    cost_price: float
    status: str


PRODUCT_NAMES = [
    "Laptop",
    "Monitor",
    "Keyboard",
    "Mouse",
    "Headphones",
    "Smartphone",
    "Tablet",
    "Television",
    "Coffee Maker",
    "Blender",
    "Desk Lamp",
    "Office Chair",
    "Backpack",
    "Running Shoes",
    "Water Bottle",
]


def generate_products(
    count: int,
    category_ids: list[int],
    supplier_ids: list[int],
    seed: int,
) -> list[Product]:
    if not category_ids:
        raise ValueError("category_ids cannot be empty")

    if not supplier_ids:
        raise ValueError("supplier_ids cannot be empty")

    rng = Random(seed)

    products: list[Product] = []

    for product_id in range(1, count + 1):
        cost_price = round(rng.uniform(10.0, 500.0), 2)

        markup = rng.uniform(1.15, 2.00)

        unit_price = round(
            cost_price * markup,
            2,
        )

        products.append(
            Product(
                product_id=product_id,
                sku=f"SKU-{product_id:08d}",
                product_name=(
                    f"{PRODUCT_NAMES[
                        (product_id - 1) % len(PRODUCT_NAMES)
                    ]} {product_id}"
                ),
                category_id=rng.choice(category_ids),
                supplier_id=rng.choice(supplier_ids),
                unit_price=unit_price,
                cost_price=cost_price,
                status="ACTIVE",
            )
        )

    return products
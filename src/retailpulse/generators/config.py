from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42

    categories: int = 10
    suppliers: int = 100
    stores: int = 20
    products: int = 1_000

    customers: int = 10_000
    orders: int = 50_000
    order_items: int = 150_000
    payments: int = 50_000
    returns: int = 5_000


DEV_CONFIG = GeneratorConfig()
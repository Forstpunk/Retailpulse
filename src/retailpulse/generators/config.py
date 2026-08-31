from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class GeneratorConfig:

    # =========================================================
    # Reproducibility
    # =========================================================

    seed: int = 42

    # =========================================================
    # Reference data
    # =========================================================

    categories: int = 10
    suppliers: int = 100
    stores: int = 20

    # =========================================================
    # Product / customer data
    # =========================================================

    products: int = 1_000
    customers: int = 10_000

    # =========================================================
    # Transactional data
    # =========================================================

    orders: int = 50_000
    order_items: int = 150_000
    payments: int = 50_000
    returns: int = 5_000

    # =========================================================
    # Generation / ingestion
    # =========================================================

    batch_size: int = 10_000

    # =========================================================
    # Transaction date range
    # =========================================================

    start_date: datetime = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    end_date: datetime = datetime(
        2026,
        12,
        31,
        23,
        59,
        59,
        tzinfo=UTC,
    )


DEV_CONFIG = GeneratorConfig()
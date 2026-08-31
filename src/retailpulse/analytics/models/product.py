from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class SourceProduct:
    product_id: int
    sku: str
    product_name: str
    category_id: int
    supplier_id: int | None
    unit_price: Decimal
    cost_price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class SourceOrder:
    order_id: int
    customer_id: int
    store_id: int | None
    order_channel: str
    order_status: str
    order_date: datetime
    currency_code: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
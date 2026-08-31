from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SourceCustomer:
    customer_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    city: str | None
    state: str | None
    country_code: str | None
    customer_segment: str
    date_of_birth: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    customer_number: str
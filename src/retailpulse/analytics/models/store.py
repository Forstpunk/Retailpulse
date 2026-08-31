from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SourceStore:
    store_id: int
    store_code: str
    store_name: str
    city: str
    state: str
    country_code: str
    region: str
    store_type: str
    opened_date: date
    status: str
    created_at: datetime
    updated_at: datetime
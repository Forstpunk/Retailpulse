from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SourceCategory:
    category_id: int
    category_name: str
    parent_category_id: int | None
    created_at: datetime
    updated_at: datetime
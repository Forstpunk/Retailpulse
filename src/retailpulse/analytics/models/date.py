from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateDimension:
    date_key: int
    full_date: date
    day_of_month: int
    day_of_week: int
    day_name: str
    week_of_year: int
    month_number: int
    month_name: str
    quarter_number: int
    year_number: int
    is_weekend: bool
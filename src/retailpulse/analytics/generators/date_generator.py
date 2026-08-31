from collections.abc import Iterator
from datetime import date, timedelta

from retailpulse.analytics.models.date import (
    DateDimension,
)


def generate_date_dimension(
    *,
    start_date: date,
    end_date: date,
) -> Iterator[DateDimension]:
    """
    Generate a contiguous date dimension.

    date_key uses YYYYMMDD format.

    Example:

        2026-01-01
        ↓
        20260101
    """

    if end_date < start_date:
        raise ValueError(
            "end_date cannot be before start_date"
        )

    current_date = start_date

    while current_date <= end_date:

        date_key = (
            current_date.year * 10_000
            + current_date.month * 100
            + current_date.day
        )

        yield DateDimension(
            date_key=date_key,
            full_date=current_date,
            day_of_month=current_date.day,
            day_of_week=current_date.isoweekday(),
            day_name=current_date.strftime("%A"),
            week_of_year=current_date.isocalendar().week,
            month_number=current_date.month,
            month_name=current_date.strftime("%B"),
            quarter_number=(
                (current_date.month - 1) // 3
            ) + 1,
            year_number=current_date.year,
            is_weekend=(
                current_date.isoweekday() >= 6
            ),
        )

        current_date += timedelta(days=1)
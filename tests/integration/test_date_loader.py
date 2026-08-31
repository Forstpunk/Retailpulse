from datetime import date

from retailpulse.analytics.generators.date_generator import (
    generate_date_dimension,
)
from retailpulse.analytics.loaders.date_loader import (
    load_dates,
)
from retailpulse.common.database import (
    get_connection,
)


def test_date_loader_is_idempotent() -> None:

    dates = list(
        generate_date_dimension(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
        )
    )

    assert len(dates) == 5

    with get_connection() as connection:

        loaded = load_dates(
            connection,
            dates,
        )

        assert loaded == 5

        loaded_again = load_dates(
            connection,
            dates,
        )

        assert loaded_again == 5

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.dim_date
                WHERE full_date >= %s
                  AND full_date <= %s
                """,
                (
                    date(2026, 1, 1),
                    date(2026, 1, 5),
                ),
            )

            count = cursor.fetchone()[0]

        assert count == 5


def test_date_dimension_attributes() -> None:

    dates = list(
        generate_date_dimension(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
        )
    )

    assert len(dates) == 1

    generated = dates[0]

    assert generated.date_key == 20260101
    assert generated.full_date == date(2026, 1, 1)

    assert generated.day_of_month == 1
    assert generated.month_number == 1
    assert generated.month_name == "January"
    assert generated.quarter_number == 1
    assert generated.year_number == 2026
    assert generated.is_weekend is False
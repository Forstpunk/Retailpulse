from collections.abc import Iterable

from psycopg import Connection

from retailpulse.analytics.models.date import (
    DateDimension,
)


def load_dates(
    connection: Connection,
    dates: Iterable[DateDimension],
) -> int:
    """
    Load generated dates into analytics.dim_date.

    Existing dates are ignored.

    Returns the number of dates processed.
    """

    dates = list(dates)

    if not dates:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        for date_dimension in dates:

            cursor.execute(
                """
                    INSERT INTO analytics.dim_date (
                        date_key,
                        full_date,
                        day_of_month,
                        day_of_week,
                        day_name,
                        week_of_year,
                        month_number,
                        month_name,
                        quarter_number,
                        year_number,
                        is_weekend
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (date_key)
                    DO NOTHING
                    """,
                (
                    date_dimension.date_key,
                    date_dimension.full_date,
                    date_dimension.day_of_month,
                    date_dimension.day_of_week,
                    date_dimension.day_name,
                    date_dimension.week_of_year,
                    date_dimension.month_number,
                    date_dimension.month_name,
                    date_dimension.quarter_number,
                    date_dimension.year_number,
                    date_dimension.is_weekend,
                ),
            )

    return len(dates)
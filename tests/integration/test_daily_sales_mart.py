from retailpulse.analytics.marts.daily_sales import (
    refresh_daily_sales,
)
from retailpulse.common.database import get_connection


def test_daily_sales_mart_can_refresh() -> None:

    with get_connection() as connection:

        loaded = refresh_daily_sales(
            connection
        )

        assert loaded >= 0

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COUNT(*)
                FROM analytics.mart_daily_sales
                """
            )

            row_count = cursor.fetchone()[0]

        assert row_count >= 0
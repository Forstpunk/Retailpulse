from retailpulse.analytics.marts.customer_performance import (
    refresh_customer_performance,
)
from retailpulse.common.database import get_connection


def test_customer_performance_mart_can_refresh() -> None:

    with get_connection() as connection:

        loaded = refresh_customer_performance(
            connection
        )

        assert loaded >= 0

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.mart_customer_performance
                """
            )

            row_count = cursor.fetchone()[0]

        assert row_count >= 0
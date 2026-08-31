from retailpulse.analytics.marts.store_performance import (
    refresh_store_performance,
)
from retailpulse.common.database import get_connection


def test_store_performance_mart_can_refresh() -> None:

    with get_connection() as connection:

        loaded = refresh_store_performance(
            connection
        )

        assert loaded >= 0

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.mart_store_performance
                """
            )

            row_count = cursor.fetchone()[0]

        assert row_count >= 0
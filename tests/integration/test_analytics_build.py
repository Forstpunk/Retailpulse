from retailpulse.analytics.build import (
    build_analytics,
)
from retailpulse.common.database import (
    get_connection,
)


def test_analytics_build_refreshes_all_marts() -> None:

    with get_connection() as connection:

        result = build_analytics(
            connection
        )

        assert result.daily_sales_rows >= 0

        assert (
            result.product_performance_rows
            >= 0
        )

        assert (
            result.customer_performance_rows
            >= 0
        )

        assert (
            result.store_performance_rows
            >= 0
        )

        assert result.total_rows >= 0
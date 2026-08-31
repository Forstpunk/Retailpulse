from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.analytics.loaders.category_loader import (
    load_categories,
)
from retailpulse.analytics.models.category import (
    SourceCategory,
)
from retailpulse.common.database import (
    get_connection,
)


def test_category_loader_is_idempotent() -> None:

    category_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    timestamp = datetime.now(
        UTC
    )

    category = SourceCategory(
        category_id=category_id,
        category_name="Test Category",
        parent_category_id=None,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        loaded = load_categories(
            connection,
            [category],
        )

        assert loaded == 1

        loaded_again = load_categories(
            connection,
            [category],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.dim_category
                WHERE category_id = %s
                """,
                (category_id,),
            )

            count = cursor.fetchone()[0]

        assert count == 1
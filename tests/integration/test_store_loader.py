from datetime import UTC, date, datetime
from uuid import uuid4

from retailpulse.analytics.loaders.store_loader import (
    load_stores,
)
from retailpulse.analytics.models.store import (
    SourceStore,
)
from retailpulse.common.database import (
    get_connection,
)


def test_store_loader_is_idempotent() -> None:

    store_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    store_code = (
        f"TEST-{uuid4().hex[:12]}"
    )

    timestamp = datetime.now(
        UTC
    )

    store = SourceStore(
        store_id=store_id,
        store_code=store_code,
        store_name="Test Store",
        city="Kochi",
        state="Kerala",
        country_code="IN",
        region="SOUTH",
        store_type="RETAIL",
        opened_date=date(
            2025,
            1,
            1,
        ),
        status="OPEN",
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        loaded = load_stores(
            connection,
            [store],
        )

        assert loaded == 1

        loaded_again = load_stores(
            connection,
            [store],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.dim_store
                WHERE store_id = %s
                """,
                (store_id,),
            )

            count = cursor.fetchone()[0]

        assert count == 1
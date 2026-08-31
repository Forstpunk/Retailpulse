from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.analytics.loaders.supplier_loader import (
    load_suppliers,
)
from retailpulse.analytics.repositories.supplier_repository import (
    SourceSupplier,
)
from retailpulse.common.database import get_connection


def test_supplier_loader_is_idempotent() -> None:

    supplier_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    timestamp = datetime.now(
        UTC
    )

    supplier = SourceSupplier(
        supplier_id=supplier_id,
        supplier_name="Test Supplier",
        country_code="IN",
        status="ACTIVE",
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        loaded = load_suppliers(
            connection,
            [supplier],
        )

        assert loaded == 1

        loaded_again = load_suppliers(
            connection,
            [supplier],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COUNT(*)
                FROM analytics.dim_supplier
                WHERE supplier_id = %s
                """,
                (supplier_id,),
            )

            count = cursor.fetchone()[0]

    assert count == 1
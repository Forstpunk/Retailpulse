from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from retailpulse.analytics.loaders.product_loader import (
    load_products,
)
from retailpulse.analytics.models.product import (
    SourceProduct,
)
from retailpulse.common.database import (
    get_connection,
)


def test_product_loader_is_idempotent() -> None:

    product_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    timestamp = datetime.now(
        UTC
    )

    product = SourceProduct(
        product_id=product_id,
        sku=f"TEST-{uuid4().hex[:12]}",
        product_name="Test Product",
        category_id=1,
        supplier_id=None,
        unit_price=Decimal("100.00"),
        cost_price=Decimal("60.00"),
        status="ACTIVE",
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        loaded = load_products(
            connection,
            [product],
        )

        assert loaded == 1

        loaded_again = load_products(
            connection,
            [product],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.dim_product
                WHERE product_id = %s
                """,
                (product_id,),
            )

            count = cursor.fetchone()[0]

        assert count == 1
from datetime import UTC, datetime
from uuid import uuid4

from retailpulse.analytics.loaders.customer_loader import (
    load_customers,
)
from retailpulse.analytics.models.customer import (
    SourceCustomer,
)
from retailpulse.common.database import (
    get_connection,
)


def test_customer_loader_is_idempotent() -> None:

    customer_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    customer_number = (
        f"TEST-{uuid4().hex[:12]}"
    )

    timestamp = datetime.now(
        UTC
    )

    customer = SourceCustomer(
        customer_id=customer_id,
        customer_number=customer_number,
        first_name="Test",
        last_name="Customer",
        email=(
            f"{uuid4().hex[:12]}"
            "@example.com"
        ),
        phone=None,
        city="Kochi",
        state="Kerala",
        country_code="IN",
        customer_segment="STANDARD",
        date_of_birth=None,
        status="ACTIVE",
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        loaded = load_customers(
            connection,
            [customer],
        )

        assert loaded == 1

        loaded_again = load_customers(
            connection,
            [customer],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM analytics.dim_customer
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

            count = cursor.fetchone()[0]

        assert count == 1
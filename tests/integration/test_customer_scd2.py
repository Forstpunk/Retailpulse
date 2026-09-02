from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from retailpulse.analytics.loaders.customer_loader import (
    load_customers,
)
from retailpulse.analytics.loaders.date_loader import (
    load_dates,
)
from retailpulse.analytics.loaders.order_fact_loader import (
    load_fact_orders,
)
from retailpulse.analytics.models.customer import (
    SourceCustomer,
)
from retailpulse.analytics.models.date import (
    DateDimension,
)
from retailpulse.analytics.models.fact_order import (
    SourceOrder,
)
from retailpulse.common.database import (
    get_connection,
)


def _customer(
    customer_id: int,
    customer_number: str,
    *,
    segment: str,
    city: str,
    updated_at: datetime,
    created_at: datetime,
) -> SourceCustomer:

    return SourceCustomer(
        customer_id=customer_id,
        customer_number=customer_number,
        first_name="SCD2",
        last_name="Test",
        email=(
            f"{uuid4().hex[:12]}@example.com"
        ),
        phone=None,
        city=city,
        state="Kerala",
        country_code="IN",
        customer_segment=segment,
        date_of_birth=None,
        status="ACTIVE",
        created_at=created_at,
        updated_at=updated_at,
    )


def test_customer_segment_change_creates_new_version() -> None:

    customer_id = (
        9_500_000
        + (uuid4().int % 100_000)
    )

    customer_number = (
        f"SCD2-{uuid4().hex[:12]}"
    )

    t1 = datetime.now(UTC)

    t2 = t1 + timedelta(days=1)

    v1 = _customer(
        customer_id,
        customer_number,
        segment="STANDARD",
        city="Kochi",
        created_at=t1,
        updated_at=t1,
    )

    v2 = _customer(
        customer_id,
        customer_number,
        segment="PREMIUM",
        city="Kochi",
        created_at=t1,
        updated_at=t2,
    )

    with get_connection() as connection:

        load_customers(connection, [v1])

        load_customers(connection, [v2])

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    customer_segment,
                    is_current,
                    valid_from,
                    valid_to
                FROM analytics.dim_customer
                WHERE customer_id = %s
                ORDER BY valid_from
                """,
                (customer_id,),
            )

            rows = cursor.fetchall()

    assert len(rows) == 2

    historical, current = rows

    assert historical[0] == "STANDARD"

    assert historical[1] is False

    assert historical[3] == t2

    assert current[0] == "PREMIUM"

    assert current[1] is True

    assert current[3] is None


def test_customer_non_segment_change_does_not_create_a_new_version() -> None:

    customer_id = (
        9_600_000
        + (uuid4().int % 100_000)
    )

    customer_number = (
        f"SCD2-{uuid4().hex[:12]}"
    )

    t1 = datetime.now(UTC)

    t2 = t1 + timedelta(days=1)

    v1 = _customer(
        customer_id,
        customer_number,
        segment="STANDARD",
        city="Kochi",
        created_at=t1,
        updated_at=t1,
    )

    v2 = _customer(
        customer_id,
        customer_number,
        segment="STANDARD",
        city="Mumbai",
        created_at=t1,
        updated_at=t2,
    )

    with get_connection() as connection:

        load_customers(connection, [v1])

        load_customers(connection, [v2])

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    city,
                    customer_segment,
                    is_current
                FROM analytics.dim_customer
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

            rows = cursor.fetchall()

    assert len(rows) == 1

    assert rows[0][0] == "Mumbai"

    assert rows[0][1] == "STANDARD"

    assert rows[0][2] is True


def test_fact_order_resolves_current_customer_version_after_segment_change() -> None:

    customer_id = (
        9_700_000
        + (uuid4().int % 100_000)
    )

    customer_number = (
        f"SCD2-{uuid4().hex[:12]}"
    )

    order_id = (
        9_700_000
        + (uuid4().int % 100_000)
    )

    t1 = datetime.now(UTC)

    t2 = t1 + timedelta(days=1)

    v1 = _customer(
        customer_id,
        customer_number,
        segment="STANDARD",
        city="Kochi",
        created_at=t1,
        updated_at=t1,
    )

    v2 = _customer(
        customer_id,
        customer_number,
        segment="VIP",
        city="Kochi",
        created_at=t1,
        updated_at=t2,
    )

    order = SourceOrder(
        order_id=order_id,
        customer_id=customer_id,
        store_id=None,
        order_channel="WEB",
        order_status="CONFIRMED",
        order_date=datetime(
            2026,
            8,
            26,
            12,
            0,
            tzinfo=UTC,
        ),
        currency_code="INR",
        subtotal_amount=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        shipping_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        created_at=t2,
        updated_at=t2,
    )

    date_dimension = DateDimension(
        date_key=20260826,
        full_date=datetime(
            2026,
            8,
            26,
        ).date(),
        day_of_month=26,
        day_of_week=3,
        day_name="Wednesday",
        week_of_year=35,
        month_number=8,
        month_name="August",
        quarter_number=3,
        year_number=2026,
        is_weekend=False,
    )

    with get_connection() as connection:

        load_dates(connection, [date_dimension])

        load_customers(connection, [v1])

        load_customers(connection, [v2])

        load_fact_orders(connection, [order])

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT dc.customer_segment
                FROM analytics.fact_order fo
                JOIN analytics.dim_customer dc
                  ON dc.customer_key = fo.customer_key
                WHERE fo.order_id = %s
                """,
                (order_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    assert row[0] == "VIP"

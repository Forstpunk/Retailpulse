from datetime import UTC, datetime
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
from retailpulse.analytics.loaders.store_loader import (
    load_stores,
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
from retailpulse.analytics.models.store import (
    SourceStore,
)
from retailpulse.common.database import (
    get_connection,
)


def test_fact_order_loader_resolves_dimension_keys() -> None:

    timestamp = datetime.now(
        UTC
    )

    customer_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    customer_number = (
        f"TEST-{uuid4().hex[:12]}"
    )

    store_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    store_code = (
        f"TEST-{uuid4().hex[:12]}"
    )

    order_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    customer = SourceCustomer(
        customer_id=customer_id,
        customer_number=customer_number,
        first_name="Fact",
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

    store = SourceStore(
        store_id=store_id,
        store_code=store_code,
        store_name="Fact Test Store",
        city="Kochi",
        state="Kerala",
        country_code="IN",
        region="SOUTH",
        store_type="RETAIL",
        opened_date=timestamp.date(),
        status="OPEN",
        created_at=timestamp,
        updated_at=timestamp,
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

    order = SourceOrder(
        order_id=order_id,
        customer_id=customer_id,
        store_id=store_id,
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
        subtotal_amount=Decimal("1000.00"),
        discount_amount=Decimal("100.00"),
        tax_amount=Decimal("90.00"),
        shipping_amount=Decimal("50.00"),
        total_amount=Decimal("1040.00"),
        created_at=timestamp,
        updated_at=timestamp,
    )

    with get_connection() as connection:

        load_customers(
            connection,
            [customer],
        )

        load_stores(
            connection,
            [store],
        )

        load_dates(
            connection,
            [date_dimension],
        )

        loaded = load_fact_orders(
            connection,
            [order],
        )

        assert loaded == 1

        loaded_again = load_fact_orders(
            connection,
            [order],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    fo.order_id,
                    fo.customer_key,
                    fo.store_key,
                    fo.order_date_key,
                    dc.customer_id,
                    ds.store_id,
                    dd.full_date
                FROM analytics.fact_order fo
                JOIN analytics.dim_customer dc
                  ON dc.customer_key = fo.customer_key
                JOIN analytics.dim_store ds
                  ON ds.store_key = fo.store_key
                JOIN analytics.dim_date dd
                  ON dd.date_key = fo.order_date_key
                WHERE fo.order_id = %s
                """,
                (order_id,),
            )

            row = cursor.fetchone()

        assert row is not None

        (
            loaded_order_id,
            customer_key,
            store_key,
            order_date_key,
            loaded_customer_id,
            loaded_store_id,
            loaded_date,
        ) = row

        assert loaded_order_id == order_id
        assert customer_key > 0
        assert store_key > 0
        assert order_date_key == 20260826

        assert loaded_customer_id == customer_id
        assert loaded_store_id == store_id
        assert loaded_date == datetime(
            2026,
            8,
            26,
        ).date()
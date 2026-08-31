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
from retailpulse.analytics.loaders.order_item_fact_loader import (
    load_fact_order_items,
)
from retailpulse.analytics.loaders.product_loader import (
    load_products,
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
from retailpulse.analytics.models.fact_order_item import (
    SourceOrderItem,
)
from retailpulse.analytics.models.product import (
    SourceProduct,
)
from retailpulse.analytics.models.store import (
    SourceStore,
)
from retailpulse.common.database import (
    get_connection,
)


def test_fact_order_item_loader_resolves_keys() -> None:

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

    product_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    product_sku = (
        f"TEST-{uuid4().hex[:12]}"
    )

    order_id = (
        9_000_000
        + (uuid4().int % 100_000)
    )

    order_item_id = (
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

    product = SourceProduct(
        product_id=product_id,
        sku=product_sku,
        product_name="Fact Test Product",
        category_id=1,
        supplier_id=None,
        unit_price=Decimal("100.00"),
        cost_price=Decimal("60.00"),
        status="ACTIVE",
        created_at=timestamp,
        updated_at=timestamp,
    )

    date_dimension = DateDimension(
        date_key=20260827,
        full_date=timestamp.date(),
        day_of_month=27,
        day_of_week=4,
        day_name="Thursday",
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
        order_date=timestamp,
        currency_code="INR",
        subtotal_amount=Decimal("200.00"),
        discount_amount=Decimal("10.00"),
        tax_amount=Decimal("19.00"),
        shipping_amount=Decimal("20.00"),
        total_amount=Decimal("229.00"),
        created_at=timestamp,
        updated_at=timestamp,
    )

    order_item = SourceOrderItem(
        order_item_id=order_item_id,
        order_id=order_id,
        product_id=product_id,
        quantity=2,
        unit_price=Decimal("100.00"),
        discount_amount=Decimal("10.00"),
        tax_amount=Decimal("19.00"),
        line_total=Decimal("209.00"),
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

        load_products(
            connection,
            [product],
        )

        load_dates(
            connection,
            [date_dimension],
        )

        load_fact_orders(
            connection,
            [order],
        )

        loaded = load_fact_order_items(
            connection,
            [order_item],
        )

        assert loaded == 1

        loaded_again = load_fact_order_items(
            connection,
            [order_item],
        )

        assert loaded_again == 1

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    foi.order_item_id,
                    foi.order_key,
                    foi.product_key,
                    fo.order_id,
                    dp.product_id,
                    foi.quantity,
                    foi.line_total
                FROM analytics.fact_order_item foi
                JOIN analytics.fact_order fo
                  ON fo.order_key = foi.order_key
                JOIN analytics.dim_product dp
                  ON dp.product_key = foi.product_key
                WHERE foi.order_item_id = %s
                """,
                (order_item_id,),
            )

            row = cursor.fetchone()

        assert row is not None

        (
            loaded_item_id,
            order_key,
            product_key,
            loaded_order_id,
            loaded_product_id,
            quantity,
            line_total,
        ) = row

        assert loaded_item_id == order_item_id

        assert order_key > 0
        assert product_key > 0

        assert loaded_order_id == order_id
        assert loaded_product_id == product_id

        assert quantity == 2
        assert line_total == Decimal("209.00")
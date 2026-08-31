from dataclasses import dataclass

from psycopg import Connection

from retailpulse.analytics.generators.date_generator import (
    generate_date_dimension,
)
from retailpulse.analytics.loaders.category_loader import (
    load_categories,
)
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
from retailpulse.analytics.loaders.supplier_loader import (
    load_suppliers,
)
from retailpulse.analytics.marts.customer_performance import (
    refresh_customer_performance,
)
from retailpulse.analytics.marts.daily_sales import (
    refresh_daily_sales,
)
from retailpulse.analytics.marts.product_performance import (
    refresh_product_performance,
)
from retailpulse.analytics.marts.store_performance import (
    refresh_store_performance,
)
from retailpulse.analytics.repositories.category_repository import (
    get_categories,
)
from retailpulse.analytics.repositories.customer_repository import (
    get_customers,
)
from retailpulse.analytics.repositories.order_item_repository import (
    get_order_items,
)
from retailpulse.analytics.repositories.order_repository import (
    get_orders,
)
from retailpulse.analytics.repositories.product_repository import (
    get_products,
)
from retailpulse.analytics.repositories.store_repository import (
    get_stores,
)
from retailpulse.analytics.repositories.supplier_repository import (
    get_suppliers,
)
from retailpulse.analytics.watermark_repository import (
    advance_watermark,
    get_watermark_int,
)

PIPELINE_NAME = "retailpulse_analytics"

ORDERS_SOURCE = "retail.orders"
ORDER_ITEMS_SOURCE = "retail.order_items"


@dataclass(frozen=True)
class AnalyticsBuildResult:
    # Dimension load counts. Dimensions are small reference
    # data, so every run re-reads and upserts the full
    # current set rather than tracking a watermark for them.
    categories_loaded: int
    suppliers_loaded: int
    products_loaded: int
    customers_loaded: int
    stores_loaded: int

    # Fact load counts. Facts are the high-volume tables, so
    # these reflect only rows extracted since the last
    # watermark (see _load_facts_incrementally).
    orders_loaded: int
    order_items_loaded: int

    # Mart refresh counts.
    daily_sales_rows: int
    product_performance_rows: int
    customer_performance_rows: int
    store_performance_rows: int

    @property
    def total_rows(self) -> int:
        return (
            self.daily_sales_rows
            + self.product_performance_rows
            + self.customer_performance_rows
            + self.store_performance_rows
        )


def _ensure_date_dimension_covers_orders(
    connection: Connection,
) -> int:
    """
    Extend analytics.dim_date to cover the full date range
    present in retail.orders, generating it on demand
    instead of requiring a separate manual bootstrap step
    (populate_date_dimension.py) to have been run first.

    Idempotent: load_dates() is ON CONFLICT DO NOTHING, and
    this is a no-op once dim_date already covers the needed
    range.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                MIN(order_date)::date,
                MAX(order_date)::date
            FROM retail.orders
            """
        )

        row = cursor.fetchone()

    if row is None or row[0] is None:
        # No orders yet — nothing to cover.
        return 0

    needed_start, needed_end = row

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT MIN(full_date), MAX(full_date)
            FROM analytics.dim_date
            """
        )

        existing_range = cursor.fetchone()
        assert existing_range is not None
        existing_min, existing_max = existing_range

    if (
        existing_min is not None
        and existing_min <= needed_start
        and existing_max >= needed_end
    ):
        return 0

    start_date = (
        min(existing_min, needed_start)
        if existing_min is not None
        else needed_start
    )

    end_date = (
        max(existing_max, needed_end)
        if existing_max is not None
        else needed_end
    )

    return load_dates(
        connection,
        generate_date_dimension(
            start_date=start_date,
            end_date=end_date,
        ),
    )


def _load_dimensions(
    connection: Connection,
) -> tuple[int, int, int, int, int]:
    """
    Full-refresh every dimension from the retail source
    schema. Dimensions are small (categories, suppliers,
    stores, products, customers), and every loader is an
    idempotent upsert, so re-reading the complete current
    set each run is simple and cheap — no watermark
    needed here (see Phase 7 notes in build_analytics's
    docstring for the volume-driven distinction from
    facts).

    Load order matters: products reference categories and
    suppliers, so those load first.
    """

    _ensure_date_dimension_covers_orders(
        connection
    )

    categories_loaded = load_categories(
        connection,
        get_categories(connection),
    )

    suppliers_loaded = load_suppliers(
        connection,
        get_suppliers(connection),
    )

    products_loaded = load_products(
        connection,
        get_products(connection),
    )

    customers_loaded = load_customers(
        connection,
        get_customers(connection),
    )

    stores_loaded = load_stores(
        connection,
        get_stores(connection),
    )

    return (
        categories_loaded,
        suppliers_loaded,
        products_loaded,
        customers_loaded,
        stores_loaded,
    )


@dataclass(frozen=True)
class _FactLoadOutcome:
    orders_loaded: int
    order_items_loaded: int
    max_order_id: int | None
    max_order_item_id: int | None


def _load_facts_incrementally(
    connection: Connection,
) -> _FactLoadOutcome:
    """
    Load only orders/order-items created since the last
    successful analytics run, using an id-based watermark
    per source (see analytics.watermark_repository).

    This does NOT advance the watermark — that is the
    caller's responsibility, and must only happen after
    the marts built from this data have also refreshed
    successfully. See build_analytics.
    """

    orders_watermark = get_watermark_int(
        connection,
        pipeline_name=PIPELINE_NAME,
        source_name=ORDERS_SOURCE,
    )

    new_orders = get_orders(
        connection,
        since_order_id=orders_watermark,
    )

    orders_loaded = load_fact_orders(
        connection,
        new_orders,
    )

    order_items_watermark = get_watermark_int(
        connection,
        pipeline_name=PIPELINE_NAME,
        source_name=ORDER_ITEMS_SOURCE,
    )

    new_order_items = get_order_items(
        connection,
        since_order_item_id=order_items_watermark,
    )

    order_items_loaded = load_fact_order_items(
        connection,
        new_order_items,
    )

    return _FactLoadOutcome(
        orders_loaded=orders_loaded,
        order_items_loaded=order_items_loaded,
        max_order_id=(
            max(
                order.order_id
                for order in new_orders
            )
            if new_orders
            else None
        ),
        max_order_item_id=(
            max(
                item.order_item_id
                for item in new_order_items
            )
            if new_order_items
            else None
        ),
    )


def build_analytics(
    connection: Connection,
) -> AnalyticsBuildResult:
    """
    Extract from the retail source schema, load the
    warehouse dimensions/facts, and refresh all
    analytical marts.

    Flow:

        load dimensions (full refresh, idempotent upsert)
                ↓
        read fact watermarks
                ↓
        extract + load only new orders/order_items
                ↓
        refresh marts from the now-current fact tables
                ↓
        advance fact watermarks

    The watermark only advances after marts refresh
    successfully — if this function raises at any point,
    nothing after that point (including the watermark
    advance) has run, so the next attempt reprocesses the
    same increment instead of silently skipping it.
    """

    (
        categories_loaded,
        suppliers_loaded,
        products_loaded,
        customers_loaded,
        stores_loaded,
    ) = _load_dimensions(connection)

    fact_outcome = _load_facts_incrementally(
        connection
    )

    daily_sales_rows = refresh_daily_sales(
        connection
    )

    product_performance_rows = (
        refresh_product_performance(
            connection
        )
    )

    customer_performance_rows = (
        refresh_customer_performance(
            connection
        )
    )

    store_performance_rows = (
        refresh_store_performance(
            connection
        )
    )

    # Advance the fact watermarks only now that the marts
    # built from this increment have also refreshed
    # successfully. If anything above raised, execution
    # never reaches here, so the next run reprocesses the
    # same increment instead of silently skipping it.

    if fact_outcome.max_order_id is not None:

        advance_watermark(
            connection,
            pipeline_name=PIPELINE_NAME,
            source_name=ORDERS_SOURCE,
            watermark_column="order_id",
            watermark_value=str(
                fact_outcome.max_order_id
            ),
        )

    if fact_outcome.max_order_item_id is not None:

        advance_watermark(
            connection,
            pipeline_name=PIPELINE_NAME,
            source_name=ORDER_ITEMS_SOURCE,
            watermark_column="order_item_id",
            watermark_value=str(
                fact_outcome.max_order_item_id
            ),
        )

    return AnalyticsBuildResult(
        categories_loaded=categories_loaded,
        suppliers_loaded=suppliers_loaded,
        products_loaded=products_loaded,
        customers_loaded=customers_loaded,
        stores_loaded=stores_loaded,
        orders_loaded=fact_outcome.orders_loaded,
        order_items_loaded=(
            fact_outcome.order_items_loaded
        ),
        daily_sales_rows=daily_sales_rows,
        product_performance_rows=(
            product_performance_rows
        ),
        customer_performance_rows=(
            customer_performance_rows
        ),
        store_performance_rows=(
            store_performance_rows
        ),
    )

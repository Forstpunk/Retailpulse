from collections.abc import Iterable

from psycopg import Connection, Cursor

from retailpulse.analytics.models.fact_order_item import (
    SourceOrderItem,
)


def _fetch_scalar(cursor: Cursor) -> int:
    row = cursor.fetchone()
    assert row is not None
    return row[0]


def load_fact_order_items(
    connection: Connection,
    order_items: Iterable[SourceOrderItem],
) -> int:
    """
    Load source order items into analytics.fact_order_item.

    Source order_id/product_id are resolved to
    fact_order/dim_product surrogate keys via a set-based
    JOIN rather than one SELECT per row — see
    order_fact_loader.load_fact_orders for why that
    matters at RetailPulse's real data volumes.

    Existing order items are updated only when the source
    record is newer.
    """

    order_items = list(order_items)

    if not order_items:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_fact_order_item_staging (
                        order_item_id BIGINT,
                        order_id BIGINT,
                        product_id BIGINT,
                        quantity INTEGER,
                        unit_price NUMERIC(12,2),
                        discount_amount NUMERIC(12,2),
                        tax_amount NUMERIC(12,2),
                        line_total NUMERIC(14,2),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_fact_order_item_staging"
        )

        with cursor.copy(
            """
                COPY tmp_fact_order_item_staging (
                    order_item_id,
                    order_id,
                    product_id,
                    quantity,
                    unit_price,
                    discount_amount,
                    tax_amount,
                    line_total,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for item in order_items:

                copy.write_row(
                    (
                        item.order_item_id,
                        item.order_id,
                        item.product_id,
                        item.quantity,
                        item.unit_price,
                        item.discount_amount,
                        item.tax_amount,
                        item.line_total,
                        item.created_at,
                        item.updated_at,
                    )
                )

        # -------------------------------------------------
        # Fail loudly on unresolvable references instead
        # of silently dropping rows from the JOIN below.
        # -------------------------------------------------

        cursor.execute(
            """
                SELECT COUNT(*)
                FROM tmp_fact_order_item_staging s
                LEFT JOIN analytics.fact_order fo
                    ON fo.order_id = s.order_id
                WHERE fo.order_key IS NULL
                """
        )

        unresolved_orders = (
            _fetch_scalar(cursor)
        )

        if unresolved_orders:
            raise ValueError(
                f"{unresolved_orders} order item(s) "
                "reference an order_id that does not "
                "exist in analytics.fact_order"
            )

        cursor.execute(
            """
                SELECT COUNT(*)
                FROM tmp_fact_order_item_staging s
                LEFT JOIN analytics.dim_product dp
                    ON dp.product_id = s.product_id
                WHERE dp.product_key IS NULL
                """
        )

        unresolved_products = (
            _fetch_scalar(cursor)
        )

        if unresolved_products:
            raise ValueError(
                f"{unresolved_products} order item(s) "
                "reference a product_id that does not "
                "exist in analytics.dim_product"
            )

        cursor.execute(
            """
                INSERT INTO analytics.fact_order_item (
                    order_item_id,
                    order_key,
                    product_key,
                    quantity,
                    unit_price,
                    discount_amount,
                    tax_amount,
                    line_total,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    s.order_item_id,
                    fo.order_key,
                    dp.product_key,
                    s.quantity,
                    s.unit_price,
                    s.discount_amount,
                    s.tax_amount,
                    s.line_total,
                    s.source_created_at,
                    s.source_updated_at
                FROM tmp_fact_order_item_staging s
                JOIN analytics.fact_order fo
                    ON fo.order_id = s.order_id
                JOIN analytics.dim_product dp
                    ON dp.product_id = s.product_id
                ON CONFLICT (order_item_id)
                DO UPDATE
                SET
                    order_key =
                        EXCLUDED.order_key,
                    product_key =
                        EXCLUDED.product_key,
                    quantity =
                        EXCLUDED.quantity,
                    unit_price =
                        EXCLUDED.unit_price,
                    discount_amount =
                        EXCLUDED.discount_amount,
                    tax_amount =
                        EXCLUDED.tax_amount,
                    line_total =
                        EXCLUDED.line_total,
                    source_created_at =
                        EXCLUDED.source_created_at,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.fact_order_item.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(order_items)

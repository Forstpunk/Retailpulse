from collections.abc import Iterable

from psycopg import Connection, Cursor

from retailpulse.analytics.models.fact_order import (
    SourceOrder,
)


def _fetch_scalar(cursor: Cursor) -> int:
    row = cursor.fetchone()
    assert row is not None
    return row[0]


def load_fact_orders(
    connection: Connection,
    orders: Iterable[SourceOrder],
) -> int:
    """
    Load source orders into analytics.fact_order.

    Business IDs from the source are resolved to
    analytical surrogate keys via a set-based JOIN rather
    than one SELECT per row: at RetailPulse's real data
    volumes (hundreds of thousands of orders per run),
    a per-row round trip is the dominant cost, so orders
    are staged in bulk via COPY and resolved/upserted in
    one statement.

    Existing orders are updated only when the source
    record is newer.
    """

    orders = list(orders)

    if not orders:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_fact_order_staging (
                        order_id BIGINT,
                        customer_id BIGINT,
                        store_id BIGINT,
                        order_channel VARCHAR(30),
                        order_status VARCHAR(30),
                        order_date TIMESTAMPTZ,
                        currency_code CHAR(3),
                        subtotal_amount NUMERIC(14,2),
                        discount_amount NUMERIC(14,2),
                        tax_amount NUMERIC(14,2),
                        shipping_amount NUMERIC(14,2),
                        total_amount NUMERIC(14,2),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_fact_order_staging"
        )

        with cursor.copy(
            """
                COPY tmp_fact_order_staging (
                    order_id,
                    customer_id,
                    store_id,
                    order_channel,
                    order_status,
                    order_date,
                    currency_code,
                    subtotal_amount,
                    discount_amount,
                    tax_amount,
                    shipping_amount,
                    total_amount,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for order in orders:

                copy.write_row(
                    (
                        order.order_id,
                        order.customer_id,
                        order.store_id,
                        order.order_channel,
                        order.order_status,
                        order.order_date,
                        order.currency_code,
                        order.subtotal_amount,
                        order.discount_amount,
                        order.tax_amount,
                        order.shipping_amount,
                        order.total_amount,
                        order.created_at,
                        order.updated_at,
                    )
                )

        # -------------------------------------------------
        # Fail loudly if a staged order references a
        # customer or order date that hasn't been loaded
        # into the corresponding dimension yet, instead of
        # silently dropping it from the JOIN below.
        # -------------------------------------------------

        cursor.execute(
            """
                SELECT COUNT(*)
                FROM tmp_fact_order_staging s
                LEFT JOIN analytics.dim_customer dc
                    ON dc.customer_id = s.customer_id
                    AND dc.is_current = TRUE
                WHERE dc.customer_key IS NULL
                """
        )

        unresolved_customers = (
            _fetch_scalar(cursor)
        )

        if unresolved_customers:
            raise ValueError(
                f"{unresolved_customers} order(s) "
                "reference a customer_id that does "
                "not exist in analytics.dim_customer"
            )

        cursor.execute(
            """
                SELECT COUNT(*)
                FROM tmp_fact_order_staging s
                LEFT JOIN analytics.dim_date dd
                    ON dd.full_date = s.order_date::date
                WHERE dd.date_key IS NULL
                """
        )

        unresolved_dates = (
            _fetch_scalar(cursor)
        )

        if unresolved_dates:
            raise ValueError(
                f"{unresolved_dates} order(s) "
                "reference an order_date that does "
                "not exist in analytics.dim_date"
            )

        cursor.execute(
            """
                INSERT INTO analytics.fact_order (
                    order_id,
                    customer_key,
                    store_key,
                    order_date_key,
                    order_channel,
                    order_status,
                    currency_code,
                    subtotal_amount,
                    discount_amount,
                    tax_amount,
                    shipping_amount,
                    total_amount,
                    source_created_at,
                    source_updated_at
                )
                SELECT
                    s.order_id,
                    dc.customer_key,
                    ds.store_key,
                    dd.date_key,
                    s.order_channel,
                    s.order_status,
                    s.currency_code,
                    s.subtotal_amount,
                    s.discount_amount,
                    s.tax_amount,
                    s.shipping_amount,
                    s.total_amount,
                    s.source_created_at,
                    s.source_updated_at
                FROM tmp_fact_order_staging s
                JOIN analytics.dim_customer dc
                    ON dc.customer_id = s.customer_id
                    AND dc.is_current = TRUE
                LEFT JOIN analytics.dim_store ds
                    ON ds.store_id = s.store_id
                JOIN analytics.dim_date dd
                    ON dd.full_date = s.order_date::date
                ON CONFLICT (order_id)
                DO UPDATE
                SET
                    customer_key =
                        EXCLUDED.customer_key,
                    store_key =
                        EXCLUDED.store_key,
                    order_date_key =
                        EXCLUDED.order_date_key,
                    order_channel =
                        EXCLUDED.order_channel,
                    order_status =
                        EXCLUDED.order_status,
                    currency_code =
                        EXCLUDED.currency_code,
                    subtotal_amount =
                        EXCLUDED.subtotal_amount,
                    discount_amount =
                        EXCLUDED.discount_amount,
                    tax_amount =
                        EXCLUDED.tax_amount,
                    shipping_amount =
                        EXCLUDED.shipping_amount,
                    total_amount =
                        EXCLUDED.total_amount,
                    source_created_at =
                        EXCLUDED.source_created_at,
                    source_updated_at =
                        EXCLUDED.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                WHERE
                    analytics.fact_order.source_updated_at
                    <
                    EXCLUDED.source_updated_at
                """
        )

    return len(orders)

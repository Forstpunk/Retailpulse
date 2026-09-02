from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection, Cursor


def _fetch_scalar(cursor: Cursor) -> int:
    row = cursor.fetchone()
    assert row is not None
    return row[0]


@dataclass(frozen=True)
class ReconciliationResult:
    batch_id: UUID

    expected_orders: int
    actual_orders: int

    expected_order_items: int
    actual_order_items: int

    duplicate_order_ids: int
    duplicate_order_item_ids: int

    orphan_order_items: int

    order_financial_mismatches: int

    passed: bool


def reconcile_transaction_batch(
    connection: Connection,
    *,
    batch_id: UUID,
    start_order_id: int,
    expected_orders: int,
    expected_order_items: int,
) -> ReconciliationResult:
    """
    Independently reconcile a completed transaction batch
    against PostgreSQL.

    This function does not modify source data.
    """

    if expected_orders < 0:
        raise ValueError(
            "expected_orders cannot be negative"
        )

    if expected_order_items < 0:
        raise ValueError(
            "expected_order_items cannot be negative"
        )

    end_order_id = (
        start_order_id + expected_orders
    )

    with connection.cursor() as cursor:

        # -----------------------------------------------------
        # 1. Actual order count
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM retail.orders
            WHERE order_id >= %s
              AND order_id < %s
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        actual_orders = _fetch_scalar(cursor)

        # -----------------------------------------------------
        # 2. Actual order-item count
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM retail.order_items oi
            JOIN retail.orders o
              ON o.order_id = oi.order_id
            WHERE o.order_id >= %s
              AND o.order_id < %s
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        actual_order_items = (
            _fetch_scalar(cursor)
        )

        # -----------------------------------------------------
        # 3. Duplicate order IDs
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM retail.orders
                WHERE order_id >= %s
                  AND order_id < %s
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        duplicate_order_ids = (
            _fetch_scalar(cursor)
        )

        # -----------------------------------------------------
        # 4. Duplicate order-item IDs
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT oi.order_item_id
                FROM retail.order_items oi
                JOIN retail.orders o
                  ON o.order_id = oi.order_id
                WHERE o.order_id >= %s
                  AND o.order_id < %s
                GROUP BY oi.order_item_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        duplicate_order_item_ids = (
            _fetch_scalar(cursor)
        )

        # -----------------------------------------------------
        # 5. Orphan order items
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM retail.order_items oi
            LEFT JOIN retail.orders o
              ON o.order_id = oi.order_id
            WHERE o.order_id IS NULL
              AND oi.order_id >= %s
              AND oi.order_id < %s
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        orphan_order_items = (
            _fetch_scalar(cursor)
        )

        # -----------------------------------------------------
        # 6. Financial reconciliation
        #
        # total_amount should equal:
        #
        # subtotal
        # - discount
        # + tax
        # + shipping
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM retail.orders
            WHERE order_id >= %s
              AND order_id < %s
              AND total_amount != (
                    subtotal_amount
                    - discount_amount
                    + tax_amount
                    + shipping_amount
              )
            """,
            (
                start_order_id,
                end_order_id,
            ),
        )

        order_financial_mismatches = (
            _fetch_scalar(cursor)
        )

    passed = all(
        (
            actual_orders == expected_orders,
            actual_order_items
            == expected_order_items,
            duplicate_order_ids == 0,
            duplicate_order_item_ids == 0,
            orphan_order_items == 0,
            order_financial_mismatches == 0,
        )
    )

    return ReconciliationResult(
        batch_id=batch_id,
        expected_orders=expected_orders,
        actual_orders=actual_orders,
        expected_order_items=expected_order_items,
        actual_order_items=actual_order_items,
        duplicate_order_ids=duplicate_order_ids,
        duplicate_order_item_ids=duplicate_order_item_ids,
        orphan_order_items=orphan_order_items,
        order_financial_mismatches=(
            order_financial_mismatches
        ),
        passed=passed,
    )
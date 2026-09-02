from psycopg import Connection, Cursor

from retailpulse.quality.models import (
    QualityCheckResult,
    QualityCheckType,
    QualityReport,
    QualityStatus,
)


def _fetch_scalar(cursor: Cursor) -> int:
    row = cursor.fetchone()
    assert row is not None
    return row[0]


def check_order_count(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id + expected_count
    )

    with connection.cursor() as cursor:

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

        actual_count = _fetch_scalar(cursor)

    passed = (
        actual_count == expected_count
    )

    return QualityCheckResult(
        check_name="order_count",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=actual_count,
        expected_value=expected_count,
        message=(
            "Order count matches expected count"
            if passed
            else (
                "Order count does not match "
                "expected count"
            )
        ),
        check_type=(
            QualityCheckType.COMPLETENESS
        ),
    )


def check_order_item_count(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id
        + expected_count
    )

    with connection.cursor() as cursor:

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

        actual_count = _fetch_scalar(cursor)

    passed = (
        actual_count == expected_count
    )

    return QualityCheckResult(
        check_name="order_item_count",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=actual_count,
        expected_value=expected_count,
        message=(
            "Order-item count matches expected count"
            if passed
            else (
                "Order-item count does not match "
                "expected count"
            )
        ),
        check_type=(
            QualityCheckType.COMPLETENESS
        ),
    )


def check_duplicate_order_ids(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id + expected_count
    )

    with connection.cursor() as cursor:

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

        duplicate_count = (
            _fetch_scalar(cursor)
        )

    passed = duplicate_count == 0

    return QualityCheckResult(
        check_name="duplicate_order_ids",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=duplicate_count,
        expected_value=0,
        message=(
            "No duplicate order IDs found"
            if passed
            else "Duplicate order IDs detected"
        ),
        check_type=(
            QualityCheckType.UNIQUENESS
        ),
    )


def check_duplicate_order_item_ids(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id + expected_count
    )

    with connection.cursor() as cursor:

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

        duplicate_count = (
            _fetch_scalar(cursor)
        )

    passed = duplicate_count == 0

    return QualityCheckResult(
        check_name="duplicate_order_item_ids",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=duplicate_count,
        expected_value=0,
        message=(
            "No duplicate order-item IDs found"
            if passed
            else "Duplicate order-item IDs detected"
        ),
        check_type=(
            QualityCheckType.UNIQUENESS
        ),
    )


def check_orphan_order_items(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id + expected_count
    )

    with connection.cursor() as cursor:

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

        orphan_count = (
            _fetch_scalar(cursor)
        )

    passed = orphan_count == 0

    return QualityCheckResult(
        check_name="orphan_order_items",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=orphan_count,
        expected_value=0,
        message=(
            "No orphan order items found"
            if passed
            else "Orphan order items detected"
        ),
        check_type=(
            QualityCheckType.REFERENTIAL_INTEGRITY
        ),
    )


def check_order_financials(
    connection: Connection,
    *,
    start_order_id: int,
    expected_count: int,
) -> QualityCheckResult:

    end_order_id = (
        start_order_id + expected_count
    )

    with connection.cursor() as cursor:

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

        mismatch_count = (
            _fetch_scalar(cursor)
        )

    passed = mismatch_count == 0

    return QualityCheckResult(
        check_name="order_financials",
        status=(
            QualityStatus.PASS
            if passed
            else QualityStatus.FAIL
        ),
        observed_value=mismatch_count,
        expected_value=0,
        message=(
            "Order financial totals reconcile"
            if passed
            else (
                "Order financial mismatches detected"
            )
        ),
        check_type=(
            QualityCheckType.FINANCIAL_CONSISTENCY
        ),
    )


def run_transaction_quality_checks(
    connection: Connection,
    *,
    start_order_id: int,
    expected_order_count: int,
    expected_order_item_count: int | None = None,
) -> QualityReport:
    """
    Run all transaction-level data quality checks.

    Returns a QualityReport containing the results
    of every applicable quality check.
    """

    checks: list[QualityCheckResult] = []

    # ---------------------------------------------------------
    # 1. Order count
    # ---------------------------------------------------------

    checks.append(
        check_order_count(
            connection,
            start_order_id=start_order_id,
            expected_count=expected_order_count,
        )
    )

    # ---------------------------------------------------------
    # 2. Order-item count
    # ---------------------------------------------------------

    if expected_order_item_count is not None:

        checks.append(
            check_order_item_count(
                connection,
                start_order_id=start_order_id,
                expected_count=expected_order_item_count,
            )
        )

    # ---------------------------------------------------------
    # 3. Duplicate order IDs
    # ---------------------------------------------------------

    checks.append(
        check_duplicate_order_ids(
            connection,
            start_order_id=start_order_id,
            expected_count=expected_order_count,
        )
    )

    # ---------------------------------------------------------
    # 4. Duplicate order-item IDs
    # ---------------------------------------------------------

    checks.append(
        check_duplicate_order_item_ids(
            connection,
            start_order_id=start_order_id,
            expected_count=expected_order_count,
        )
    )

    # ---------------------------------------------------------
    # 5. Orphan order items
    # ---------------------------------------------------------

    checks.append(
        check_orphan_order_items(
            connection,
            start_order_id=start_order_id,
            expected_count=expected_order_count,
        )
    )

    # ---------------------------------------------------------
    # 6. Financial reconciliation
    # ---------------------------------------------------------

    checks.append(
        check_order_financials(
            connection,
            start_order_id=start_order_id,
            expected_count=expected_order_count,
        )
    )

    return QualityReport(
        checks=tuple(checks)
    )
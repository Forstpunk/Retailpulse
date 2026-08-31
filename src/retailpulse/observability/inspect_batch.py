from __future__ import annotations

import sys
from uuid import UUID

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.observability.metrics_repository import (
    get_batch_metrics,
)


def print_batch_metrics(
    batch_id: UUID,
) -> int:
    """
    Print operational information for one
    ingestion batch.

    Returns
    -------
    int
        0 when the batch exists and can be inspected.

        1 when the batch does not exist.
    """

    with get_connection() as connection:

        metrics = get_batch_metrics(
            connection,
            batch_id=batch_id,
        )

    if metrics is None:

        print()
        print(
            f"Batch not found: {batch_id}"
        )

        return 1

    print()

    print(
        "=" * 64
    )

    print(
        "RETAILPULSE INGESTION BATCH"
    )

    print(
        "=" * 64
    )

    print()

    print(
        f"Batch ID        : "
        f"{metrics.batch_id}"
    )

    print(
        f"Status          : "
        f"{metrics.status}"
    )

    print(
        f"Attempts        : "
        f"{metrics.attempt_count} / "
        f"{metrics.max_attempts}"
    )

    print()

    print(
        f"Records         : "
        f"{metrics.record_count:,}"
    )

    print(
        f"Physical Parts  : "
        f"{metrics.completed_parts} / "
        f"{metrics.total_parts}"
    )

    print(
        f"Failed Parts    : "
        f"{metrics.failed_parts}"
    )

    print()

    if metrics.duration_seconds is None:

        print(
            "Duration        : running"
        )

    else:

        print(
            f"Duration        : "
            f"{metrics.duration_seconds:.2f}s"
        )

    if metrics.orders_per_second is None:

        print(
            "Throughput      : N/A"
        )

    else:

        print(
            f"Throughput      : "
            f"{metrics.orders_per_second:,.2f} "
            "orders/sec"
        )

    print()

    print(
        f"Quality Checks  : "
        f"{metrics.quality_checks}"
    )

    print(
        f"Quality Failures: "
        f"{metrics.quality_failures}"
    )

    print()

    print(
        "-" * 64
    )

    print(
        "HEALTH"
    )

    print(
        "-" * 64
    )

    batch_healthy = (
        metrics.status == "COMPLETED"
    )

    parts_healthy = (
        metrics.failed_parts == 0
        and (
            metrics.total_parts == 0
            or metrics.completed_parts
            == metrics.total_parts
        )
    )

    quality_healthy = (
        metrics.quality_failures == 0
    )

    print(
        "Batch            : "
        f"{'HEALTHY' if batch_healthy else 'UNHEALTHY'}"
    )

    print(
        "Physical Parts   : "
        f"{'HEALTHY' if parts_healthy else 'UNHEALTHY'}"
    )

    print(
        "Quality          : "
        f"{'HEALTHY' if quality_healthy else 'UNHEALTHY'}"
    )

    print()

    overall_healthy = (
        batch_healthy
        and parts_healthy
        and quality_healthy
    )

    print(
        "Overall          : "
        f"{'HEALTHY' if overall_healthy else 'UNHEALTHY'}"
    )

    print()

    print(
        "=" * 64
    )

    return 0 if overall_healthy else 2


def main() -> None:
    """
    CLI entry point.
    """

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  uv run python -m "
            "retailpulse.observability.inspect_batch "
            "<batch_id>"
        )

        raise SystemExit(1)

    raw_batch_id = sys.argv[1]

    try:

        batch_id = UUID(raw_batch_id)

    except ValueError:

        print(
            f"Invalid batch ID: {raw_batch_id}"
        )

        raise SystemExit(1)

    exit_code = print_batch_metrics(
        batch_id
    )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
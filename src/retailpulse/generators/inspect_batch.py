from __future__ import annotations

import sys
from uuid import UUID

from retailpulse.common.database import get_connection
from retailpulse.generators.ingestion_observability import (
    BatchPartSummary,
    BatchSummary,
    QualitySummary,
    get_batch_parts_summary,
    get_batch_summary,
    get_quality_summary,
)


def format_duration(
    seconds: float | None,
) -> str:
    if seconds is None:
        return "N/A"

    return f"{seconds:.3f}s"


def print_batch_summary(
    batch: BatchSummary,
) -> None:
    print()
    print("=" * 60)
    print("RetailPulse Ingestion Batch")
    print("=" * 60)

    print()
    print(f"Batch ID       : {batch.batch_id}")
    print(f"Source         : {batch.source_system}")
    print(f"Type           : {batch.batch_type}")
    print(f"Status         : {batch.status}")

    print()
    print(f"Records        : {batch.record_count:,}")
    print(
        f"Attempts       : "
        f"{batch.attempt_count} / "
        f"{batch.max_attempts}"
    )

    print()
    print(
        f"Started        : "
        f"{batch.started_at}"
    )

    print(
        f"Completed      : "
        f"{batch.completed_at or 'N/A'}"
    )

    print(
        f"Last attempt   : "
        f"{batch.last_attempt_at}"
    )

    print(
        f"Last heartbeat : "
        f"{batch.last_heartbeat_at}"
    )

    print(
        f"Duration       : "
        f"{format_duration(batch.duration_seconds)}"
    )

    if batch.error_message:
        print()
        print(
            f"Error          : "
            f"{batch.error_message}"
        )


def print_batch_parts(
    parts: list[BatchPartSummary],
) -> None:
    print()
    print("-" * 60)
    print("Physical Parts")
    print("-" * 60)

    if not parts:
        print()
        print("No physical parts found.")
        return

    print()
    print(
        f"{'Part':<6}"
        f"{'Status':<14}"
        f"{'Orders':>10}"
        f"{'Items':>10}"
        f"{'Duration':>12}"
    )

    print(
        f"{'-' * 5:<6}"
        f"{'-' * 12:<14}"
        f"{'-' * 8:>10}"
        f"{'-' * 8:>10}"
        f"{'-' * 10:>12}"
    )

    for part in parts:
        print(
            f"{part.part_number:<6}"
            f"{part.status:<14}"
            f"{part.record_count:>10,}"
            f"{part.order_item_count:>10,}"
            f"{format_duration(part.duration_seconds):>12}"
        )

        if part.error_message:
            print(
                f"       Error: "
                f"{part.error_message}"
            )


def print_quality_results(
    quality_results: list[QualitySummary],
) -> None:
    print()
    print("-" * 60)
    print("Quality Checks")
    print("-" * 60)

    if not quality_results:
        print()
        print("No quality results found.")
        return

    print()
    print(
        f"{'Check':<32}"
        f"{'Status':<10}"
        f"{'Observed':<15}"
        f"{'Expected':<15}"
    )

    print(
        f"{'-' * 31:<32}"
        f"{'-' * 8:<10}"
        f"{'-' * 12:<15}"
        f"{'-' * 12:<15}"
    )

    for result in quality_results:

        observed = (
            result.observed_value
            if result.observed_value is not None
            else "N/A"
        )

        expected = (
            result.expected_value
            if result.expected_value is not None
            else "N/A"
        )

        print(
            f"{result.check_name:<32}"
            f"{result.status:<10}"
            f"{observed!s:<15}"
            f"{expected!s:<15}"
        )

        if result.message:
            print(
                f"       {result.message}"
            )


def print_summary_statistics(
    batch: BatchSummary,
    parts: list[BatchPartSummary],
    quality_results: list[QualitySummary],
) -> None:
    completed_parts = sum(
        1
        for part in parts
        if part.status == "COMPLETED"
    )

    failed_parts = sum(
        1
        for part in parts
        if part.status == "FAILED"
    )

    started_parts = sum(
        1
        for part in parts
        if part.status == "STARTED"
    )

    quality_passed = sum(
        1
        for result in quality_results
        if result.status == "PASS"
    )

    quality_failed = sum(
        1
        for result in quality_results
        if result.status == "FAIL"
    )

    total_order_items = sum(
        part.order_item_count
        for part in parts
        if part.status == "COMPLETED"
    )

    print()
    print("-" * 60)
    print("Operational Summary")
    print("-" * 60)

    print()
    print(
        f"Physical parts   : {len(parts):,}"
    )

    print(
        f"Completed parts  : {completed_parts:,}"
    )

    print(
        f"Started parts    : {started_parts:,}"
    )

    print(
        f"Failed parts     : {failed_parts:,}"
    )

    print(
        f"Orders loaded    : {batch.record_count:,}"
    )

    print(
        f"Order items      : "
        f"{total_order_items:,}"
    )

    print()
    print(
        f"Quality checks   : "
        f"{len(quality_results):,}"
    )

    print(
        f"Quality passed   : "
        f"{quality_passed:,}"
    )

    print(
        f"Quality failed   : "
        f"{quality_failed:,}"
    )


def inspect_batch(
    batch_id: UUID,
) -> int:
    with get_connection() as connection:

        batch = get_batch_summary(
            connection,
            batch_id=batch_id,
        )

        if batch is None:
            print()
            print(
                f"Batch not found: {batch_id}"
            )
            return 1

        parts = get_batch_parts_summary(
            connection,
            batch_id=batch_id,
        )

        quality_results = get_quality_summary(
            connection,
            batch_id=batch_id,
        )

    print_batch_summary(batch)

    print_batch_parts(parts)

    print_quality_results(
        quality_results
    )

    print_summary_statistics(
        batch,
        parts,
        quality_results,
    )

    print()

    return 0


def parse_batch_id(
    value: str,
) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid batch ID: {value}"
        ) from exc


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage:"
        )
        print(
            "  uv run python "
            "-m retailpulse.generators.inspect_batch "
            "<batch_id>"
        )
        raise SystemExit(1)

    try:
        batch_id = parse_batch_id(
            sys.argv[1]
        )
    except ValueError as exc:
        print()
        print(f"Error: {exc}")
        raise SystemExit(1)

    exit_code = inspect_batch(
        batch_id
    )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
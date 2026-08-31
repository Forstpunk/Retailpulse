from __future__ import annotations

import sys

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.observability.metrics_repository import (
    list_batch_summaries,
)


def main() -> None:

    limit = 20

    if len(sys.argv) > 2:

        print(
            "Usage:"
        )

        print(
            "  uv run python -m "
            "retailpulse.observability.list_batches "
            "[limit]"
        )

        raise SystemExit(1)

    if len(sys.argv) == 2:

        try:

            limit = int(sys.argv[1])

        except ValueError:

            print(
                f"Invalid limit: {sys.argv[1]}"
            )

            raise SystemExit(1)

    if limit <= 0:

        print(
            "Limit must be greater than zero."
        )

        raise SystemExit(1)

    with get_connection() as connection:

        batches = list_batch_summaries(
            connection,
            limit=limit,
        )

    print()

    print(
        "=" * 100
    )

    print(
        "RETAILPULSE INGESTION BATCHES"
    )

    print(
        "=" * 100
    )

    print()

    if not batches:

        print(
            "No ingestion batches found."
        )

        return

    print(
        f"{'Batch ID':<38}"
        f"{'Status':<12}"
        f"{'Records':>10}"
        f"{'Attempts':>12}"
        f"{'Duration':>14}"
    )

    print(
        "-" * 100
    )

    for batch in batches:

        if batch.duration_seconds is None:

            duration = "running"

        else:

            duration = (
                f"{batch.duration_seconds:.2f}s"
            )

        attempts = (
            f"{batch.attempt_count}"
            f"/"
            f"{batch.max_attempts}"
        )

        print(
            f"{batch.batch_id!s:<38}"
            f"{batch.status:<12}"
            f"{batch.record_count:>10,}"
            f"{attempts:>12}"
            f"{duration:>14}"
        )

    print()

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()
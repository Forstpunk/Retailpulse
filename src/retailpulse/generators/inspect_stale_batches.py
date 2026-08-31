from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.ingestion_repository import (
    get_stale_started_batches,
)

STALE_AFTER_SECONDS = 300


def main() -> None:

    with get_connection() as connection:

        batches = get_stale_started_batches(
            connection,
            stale_after_seconds=(
                STALE_AFTER_SECONDS
            ),
        )

    print()
    print("=" * 80)
    print("RetailPulse Stale Ingestion Batches")
    print("=" * 80)

    print()
    print(
        f"Stale threshold: "
        f"{STALE_AFTER_SECONDS} seconds"
    )

    if not batches:

        print()
        print(
            "No stale STARTED batches found."
        )

        return

    print()

    print(
        f"{'Batch ID':<38}"
        f"{'Source':<24}"
        f"{'Attempt':<10}"
        f"{'Started'}"
    )

    print(
        "-" * 80
    )

    for batch in batches:

        print(
            f"{batch.batch_id!s:<38}"
            f"{batch.source_system:<24}"
            f"{batch.attempt_count:<10}"
            f"{batch.started_at}"
        )

    print()

    print(
        f"Found {len(batches):,} stale "
        "STARTED batch(es)."
    )

    print()
    print(
        "No batch state was modified."
    )


if __name__ == "__main__":
    main()
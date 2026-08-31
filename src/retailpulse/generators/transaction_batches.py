from collections.abc import Iterator

from retailpulse.generators.transactions import (
    OrderTransaction,
)


def batch_transactions(
    transactions: Iterator[OrderTransaction],
    batch_size: int,
) -> Iterator[list[OrderTransaction]]:
    """
    Split a lazy transaction stream into bounded batches.
    """

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than zero"
        )

    batch: list[OrderTransaction] = []

    for transaction in transactions:
        batch.append(transaction)

        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
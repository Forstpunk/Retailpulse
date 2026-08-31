from collections.abc import Iterable, Iterator
from itertools import islice
from typing import TypeVar

T = TypeVar("T")


def batched(
    items: Iterable[T],
    batch_size: int,
) -> Iterator[list[T]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    iterator = iter(items)

    while batch := list(islice(iterator, batch_size)):
        yield batch
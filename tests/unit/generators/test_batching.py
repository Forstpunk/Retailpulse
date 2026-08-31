import pytest

from retailpulse.generators.batching import batched


def test_batches_items():
    result = list(
        batched(
            range(10),
            batch_size=3,
        )
    )

    assert result == [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [9],
    ]


def test_exact_batch_size():
    result = list(
        batched(
            range(6),
            batch_size=3,
        )
    )

    assert result == [
        [0, 1, 2],
        [3, 4, 5],
    ]


def test_empty_input():
    result = list(
        batched(
            [],
            batch_size=100,
        )
    )

    assert result == []


def test_invalid_batch_size():
    with pytest.raises(ValueError):
        list(
            batched(
                range(10),
                batch_size=0,
            )
        )


def test_large_batch_size():
    result = list(
        batched(
            range(5),
            batch_size=100,
        )
    )

    assert result == [
        [0, 1, 2, 3, 4],
    ]
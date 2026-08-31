from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from typing import TypeVar

from retailpulse.pipeline.errors import (
    DataQualityError,
)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:

    max_attempts: int = 3

    base_delay_seconds: float = 1.0

    enabled: bool = True

    def __post_init__(self) -> None:

        if self.max_attempts < 1:

            raise ValueError(
                "max_attempts must be >= 1"
            )

        if self.base_delay_seconds < 0:

            raise ValueError(
                "base_delay_seconds must be >= 0"
            )


AttemptCallback = Callable[
    [int, Exception | None],
    None,
]


def run_with_retry(
    operation: Callable[[], T],
    *,
    operation_name: str,
    retry_config: RetryConfig | None = None,
    on_attempt: AttemptCallback | None = None,
) -> T:
    """
    Execute an operation with retry support.

    Data-quality failures are never retried.

    Other exceptions are retried according to
    RetryConfig.
    """

    config = (
        retry_config
        or RetryConfig()
    )

    attempts = (
        config.max_attempts
        if config.enabled
        else 1
    )

    for attempt in range(
        1,
        attempts + 1,
    ):

        try:

            result = operation()

            if on_attempt is not None:

                on_attempt(
                    attempt,
                    None,
                )

            return result

        except DataQualityError as exc:

            if on_attempt is not None:

                on_attempt(
                    attempt,
                    exc,
                )

            raise

        except Exception as exc:

            if on_attempt is not None:

                on_attempt(
                    attempt,
                    exc,
                )

            if attempt >= attempts:

                raise

            delay = (
                config.base_delay_seconds
                * (
                    2 ** (attempt - 1)
                )
            )

            sleep(delay)

    raise RuntimeError(
        "Retry execution unexpectedly "
        f"exhausted for {operation_name}"
    )
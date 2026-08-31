from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3

    def can_retry(
        self,
        attempt_count: int,
    ) -> bool:
        return attempt_count < self.max_attempts
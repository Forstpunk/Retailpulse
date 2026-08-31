from retailpulse.generators.retry_policy import (
    RetryPolicy,
)


def test_retry_allowed_before_max_attempts() -> None:
    policy = RetryPolicy(max_attempts=3)

    assert policy.can_retry(1) is True
    assert policy.can_retry(2) is True


def test_retry_not_allowed_at_max_attempts() -> None:
    policy = RetryPolicy(max_attempts=3)

    assert policy.can_retry(3) is False
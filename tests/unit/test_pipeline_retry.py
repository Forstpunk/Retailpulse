from retailpulse.pipeline.errors import (
    DataQualityError,
    TransientPipelineError,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
    run_with_retry,
)


def test_successful_operation_runs_once() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        return "success"

    result = run_with_retry(
        operation,
        operation_name="test_operation",
    )

    assert result == "success"

    assert calls == 1


def test_transient_failure_is_retried() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        if calls < 3:
            raise TransientPipelineError(
                "temporary failure"
            )

        return "success"

    retry_config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0,
        enabled=True,
    )

    result = run_with_retry(
        operation,
        operation_name="test_retry",
        retry_config=retry_config,
    )

    assert result == "success"

    assert calls == 3


def test_non_transient_failure_is_not_retried() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        raise DataQualityError(
            "invalid transaction"
        )

    retry_config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0,
        enabled=True,
    )

    try:

        run_with_retry(
            operation,
            operation_name="test_quality",
            retry_config=retry_config,
        )

    except DataQualityError:
        pass

    else:
        raise AssertionError(
            "Expected DataQualityError"
        )

    assert calls == 1


def test_retry_limit_is_respected() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        raise TransientPipelineError(
            "temporary failure"
        )

    retry_config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0,
        enabled=True,
    )

    try:

        run_with_retry(
            operation,
            operation_name="test_limit",
            retry_config=retry_config,
        )

    except TransientPipelineError:
        pass

    else:
        raise AssertionError(
            "Expected TransientPipelineError"
        )

    assert calls == 3


def test_retry_config_defaults() -> None:

    config = RetryConfig()

    assert config.max_attempts == 3

    assert config.base_delay_seconds == 1.0

    assert config.enabled is True


def test_retry_config_rejects_invalid_attempts() -> None:

    try:

        RetryConfig(
            max_attempts=0
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_retry_can_be_disabled() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        return "success"

    retry_config = RetryConfig(
        max_attempts=5,
        base_delay_seconds=0,
        enabled=False,
    )

    result = run_with_retry(
        operation,
        operation_name="disabled_retry",
        retry_config=retry_config,
    )

    assert result == "success"

    assert calls == 1
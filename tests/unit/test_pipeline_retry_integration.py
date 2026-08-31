from retailpulse.pipeline.errors import (
    TransientPipelineError,
)
from retailpulse.pipeline.retry import (
    RetryConfig,
    run_with_retry,
)


def test_analytics_style_operation_retries() -> None:

    attempts = 0

    def build_analytics() -> dict[str, int]:
        nonlocal attempts

        attempts += 1

        if attempts < 3:
            raise TransientPipelineError(
                "temporary analytics failure"
            )

        return {
            "rows": 100,
        }

    retry_config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=0,
        enabled=True,
    )

    result = run_with_retry(
        build_analytics,
        operation_name="analytics_build",
        retry_config=retry_config,
    )

    assert result == {
        "rows": 100,
    }

    assert attempts == 3


def test_retry_can_be_disabled() -> None:

    calls = 0

    def operation() -> str:
        nonlocal calls

        calls += 1

        return "success"

    config = RetryConfig(
        max_attempts=5,
        base_delay_seconds=0,
        enabled=False,
    )

    result = run_with_retry(
        operation,
        operation_name="disabled_retry",
        retry_config=config,
    )

    assert result == "success"

    assert calls == 1
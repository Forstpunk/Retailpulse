class InjectedFailure(RuntimeError):
    """Raised when a test failure is deliberately injected."""


def should_fail(
    *,
    part_number: int,
    failure_part: int | None,
) -> bool:
    """
    Return True when failure should be injected
    for the requested physical batch.
    """

    return (
        failure_part is not None
        and part_number == failure_part
    )
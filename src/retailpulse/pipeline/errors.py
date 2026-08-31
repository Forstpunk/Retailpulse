from enum import StrEnum


class PipelineErrorCategory(StrEnum):
    TRANSIENT = "TRANSIENT"

    DATA_QUALITY = "DATA_QUALITY"

    DATABASE = "DATABASE"

    CONFIGURATION = "CONFIGURATION"

    UNKNOWN = "UNKNOWN"


class PipelineError(Exception):
    """
    Base exception for pipeline failures.
    """

    def __init__(
        self,
        message: str,
        *,
        category: PipelineErrorCategory,
    ) -> None:

        super().__init__(message)

        self.category = category


class TransientPipelineError(
    PipelineError
):
    """
    Error that may succeed if retried.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        super().__init__(
            message,
            category=(
                PipelineErrorCategory.TRANSIENT
            ),
        )


class DataQualityError(
    PipelineError
):
    """
    Error caused by invalid or inconsistent data.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        super().__init__(
            message,
            category=(
                PipelineErrorCategory.DATA_QUALITY
            ),
        )


class ConfigurationError(
    PipelineError
):
    """
    Error caused by invalid pipeline configuration.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        super().__init__(
            message,
            category=(
                PipelineErrorCategory.CONFIGURATION
            ),
        )


class DuplicateLogicalRunError(
    PipelineError
):
    """
    Raised when a logical_run_id already has a
    pipeline_runs row.

    The unique index on
    analytics.pipeline_runs.logical_run_id is the
    actual safety boundary: this exception is only
    ever raised *after* the database has rejected (or
    would have rejected) a concurrent insert, so it is
    race-safe by construction rather than by an
    application-level check-then-insert.
    """

    def __init__(
        self,
        *,
        logical_run_id: str,
        existing_pipeline_run_id: str,
        existing_status: str,
    ) -> None:

        self.logical_run_id = (
            logical_run_id
        )

        self.existing_pipeline_run_id = (
            existing_pipeline_run_id
        )

        self.existing_status = (
            existing_status
        )

        super().__init__(
            f"logical_run_id '{logical_run_id}' "
            "already has a pipeline run "
            f"(pipeline_run_id={existing_pipeline_run_id}, "
            f"status={existing_status})",
            category=(
                PipelineErrorCategory.CONFIGURATION
            ),
        )


def classify_pipeline_error(
    exc: Exception,
) -> PipelineErrorCategory:
    """
    Classify an arbitrary pipeline exception.

    Explicit PipelineError subclasses take precedence.
    Unknown exceptions are classified as UNKNOWN.
    """

    # ---------------------------------------------------------
    # Explicit pipeline errors
    # ---------------------------------------------------------

    if isinstance(
        exc,
        PipelineError,
    ):
        return exc.category

    # ---------------------------------------------------------
    # Database / infrastructure errors
    #
    # This is intentionally simple for now.
    # We will replace string matching with PostgreSQL
    # exception classes when we build the retry layer.
    # ---------------------------------------------------------

    error_message = str(
        exc
    ).lower()

    if any(
        value in error_message
        for value in (
            "connection refused",
            "connection reset",
            "connection timeout",
            "timeout",
            "deadlock",
            "too many connections",
        )
    ):
        return PipelineErrorCategory.TRANSIENT

    if any(
        value in error_message
        for value in (
            "undefined table",
            "undefined column",
            "foreign key",
            "unique constraint",
            "not-null",
            "not null",
        )
    ):
        return PipelineErrorCategory.DATABASE

    # ---------------------------------------------------------
    # Anything we don't explicitly understand.
    # ---------------------------------------------------------

    return PipelineErrorCategory.UNKNOWN
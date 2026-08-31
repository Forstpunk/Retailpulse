from retailpulse.pipeline.errors import (
    ConfigurationError,
    DataQualityError,
    PipelineErrorCategory,
    TransientPipelineError,
    classify_pipeline_error,
)


def test_transient_error_category() -> None:

    error = TransientPipelineError(
        "database connection timeout"
    )

    assert (
        classify_pipeline_error(error)
        == PipelineErrorCategory.TRANSIENT
    )


def test_quality_error_category() -> None:

    error = DataQualityError(
        "transaction quality gate failed"
    )

    assert (
        classify_pipeline_error(error)
        == PipelineErrorCategory.DATA_QUALITY
    )


def test_configuration_error_category() -> None:

    error = ConfigurationError(
        "invalid generator configuration"
    )

    assert (
        classify_pipeline_error(error)
        == PipelineErrorCategory.CONFIGURATION
    )


def test_unknown_error_category() -> None:

    error = RuntimeError(
        "something unexpected happened"
    )

    assert (
        classify_pipeline_error(error)
        == PipelineErrorCategory.UNKNOWN
    )
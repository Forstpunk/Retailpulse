from uuid import uuid4

from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.pipeline.models import (
    PipelineStatus,
)
from retailpulse.pipeline.runner import (
    run_pipeline,
)


def test_pipeline_runs_successfully() -> None:

    config = GeneratorConfig(
        seed=12345,
        categories=10,
        suppliers=10,
        stores=5,
        products=50,
        customers=100,
        orders=20,
        order_items=50,
        payments=20,
        returns=5,
        batch_size=10,
    )

    with get_connection() as connection:

        result = run_pipeline(
            connection,
            config,
            logical_run_id=(
            f"pipeline-integration-test-{uuid4()}"),
        )

    assert (
        result.status
        == PipelineStatus.SUCCESS
    )

    assert result.ingestion_completed

    assert result.quality_passed

    assert result.analytics_completed

    assert result.batch_id is not None

    assert result.orders_loaded == 20

    assert result.order_items_loaded > 0

    assert result.analytics_rows >= 0
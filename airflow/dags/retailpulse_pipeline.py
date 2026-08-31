"""RetailPulse orchestration DAG.

Per docs/architecture/decisions/ADR-002-orchestration.md,
Airflow owns scheduling, retries, dependencies, backfills,
and workflow-level observability — it does not perform data
transformations itself. This DAG is a thin scheduling shell
around retailpulse.pipeline.runner.run_pipeline(), which
already owns pipeline lifecycle tracking, stage-level retry,
and error classification (see src/retailpulse/pipeline/).

This intentionally does NOT duplicate that retry logic at
the Airflow layer: run_pipeline() retries each stage
internally (see DEFAULT_RETRY_CONFIG in pipeline/runner.py)
before ever raising, so this DAG's own retries exist only as
a second line of defense for failures the pipeline could not
resolve itself (e.g. the database being unreachable). Keeping
both layers is deliberate, not accidental duplication: the
inner layer handles transient stage failures fast and
observably (pipeline_stage_runs); the outer layer handles
"the whole run needs to be retried later" per Airflow's own
scheduling model.

Deployment note: this DAG imports the retailpulse package
directly, so it must run in (or alongside) an Airflow
environment where `retailpulse` is installed on the worker's
PYTHONPATH. It is not part of this project's own dependency
tree (see pyproject.toml) — Airflow is not installed here
deliberately, since apache-airflow does not yet support this
project's Python version, and pulling in an orchestrator's
full dependency footprint just to host one DAG file would
violate the "keep it lightweight" principle this project
follows throughout. Copy this file into an Airflow
deployment's dags/ folder to run it for real.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.exceptions import AirflowException


@dag(
    dag_id="retailpulse_pipeline",
    description=(
        "Transaction ingestion -> quality -> analytics build"
    ),
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # logical-run idempotency already
                        # prevents overlap at the DB level
                        # (see pipeline/repository.py), but
                        # there is no reason to let Airflow
                        # launch a run it knows will be
                        # SKIPPED.
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["retailpulse"],
)
def retailpulse_pipeline() -> None:

    @task
    def run() -> dict:

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

        # Airflow's own data_interval_start would replace
        # this with a real scheduling-driven value in a
        # production DAG; kept literal here since this file
        # is a template, not a deployed DAG.
        logical_run_id = "airflow-retailpulse-{{ ds }}"

        with get_connection() as connection:

            result = run_pipeline(
                connection,
                GeneratorConfig(),
                logical_run_id=logical_run_id,
            )

        if result.status == PipelineStatus.FAILED:

            raise AirflowException(
                f"RetailPulse pipeline failed: "
                f"{result.message} "
                f"(error_category="
                f"{result.error_category})"
            )

        return {
            "status": result.status.value,
            "pipeline_run_id": result.pipeline_run_id,
            "orders_loaded": result.orders_loaded,
            "analytics_rows": result.analytics_rows,
        }

    run()


retailpulse_pipeline()

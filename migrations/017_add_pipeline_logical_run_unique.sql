BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_pipeline_runs_logical_run_id
ON analytics.pipeline_runs (
    logical_run_id
);

COMMIT;
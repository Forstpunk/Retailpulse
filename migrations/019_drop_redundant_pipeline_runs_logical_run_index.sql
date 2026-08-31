-- The unique index added in 017 (uq_pipeline_runs_logical_run_id)
-- already enforces and serves every lookup that the original
-- plain index (idx_pipeline_runs_logical_run, from 016) provided.
-- Keeping both wastes write overhead on every pipeline_runs insert.

BEGIN;

DROP INDEX IF EXISTS analytics.idx_pipeline_runs_logical_run;

COMMIT;

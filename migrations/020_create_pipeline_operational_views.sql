-- Operational observability views over pipeline_runs /
-- pipeline_stage_runs. These are read-only conveniences
-- for ops/on-call use (dashboards, ad-hoc SQL) — no
-- application code depends on their column shape being
-- stable, so they can be adjusted in a later migration
-- without a data migration.

BEGIN;

-- -----------------------------------------------------------
-- v_latest_pipeline_runs
--
-- Recent pipeline activity, newest first, with a computed
-- age so an operator can see stuck/long-running executions
-- at a glance.
-- -----------------------------------------------------------

CREATE OR REPLACE VIEW analytics.v_latest_pipeline_runs AS
SELECT
    pr.pipeline_run_id,
    pr.logical_run_id,
    pr.status,
    pr.started_at,
    pr.completed_at,
    pr.duration_seconds,
    EXTRACT(
        EPOCH FROM (
            CURRENT_TIMESTAMP - pr.started_at
        )
    ) AS age_seconds,
    pr.batch_id,
    pr.orders_loaded,
    pr.order_items_loaded,
    pr.analytics_rows
FROM analytics.pipeline_runs pr
ORDER BY pr.started_at DESC;

-- -----------------------------------------------------------
-- v_pipeline_stage_summary
--
-- One row per (pipeline_run_id, stage_name), summarizing
-- every attempt made for that stage.
-- -----------------------------------------------------------

CREATE OR REPLACE VIEW analytics.v_pipeline_stage_summary AS
SELECT
    psr.pipeline_run_id,
    psr.stage_name,
    COUNT(*) AS attempt_count,
    MAX(psr.attempt) FILTER (
        WHERE psr.status = 'SUCCESS'
    ) AS successful_attempt,
    SUM(psr.duration_ms) AS total_duration_ms,
    (
        ARRAY_AGG(
            psr.records_processed
            ORDER BY psr.attempt DESC
        )
    )[1] AS records_processed,
    (
        ARRAY_AGG(
            psr.status
            ORDER BY psr.attempt DESC
        )
    )[1] AS final_status
FROM analytics.pipeline_stage_runs psr
GROUP BY
    psr.pipeline_run_id,
    psr.stage_name;

-- -----------------------------------------------------------
-- v_pipeline_failures
--
-- Every failed stage attempt, with enough pipeline context
-- to triage without a second query.
-- -----------------------------------------------------------

CREATE OR REPLACE VIEW analytics.v_pipeline_failures AS
SELECT
    psr.pipeline_run_id,
    pr.logical_run_id,
    psr.stage_name,
    psr.attempt,
    psr.error_category,
    psr.error_message,
    psr.started_at,
    psr.completed_at
FROM analytics.pipeline_stage_runs psr
JOIN analytics.pipeline_runs pr
    ON pr.pipeline_run_id = psr.pipeline_run_id
WHERE psr.status = 'FAILED'
ORDER BY psr.started_at DESC;

-- -----------------------------------------------------------
-- v_pipeline_health
--
-- One row per pipeline run with the terminal failure
-- (if any) and total retry count rolled up from
-- pipeline_stage_runs.
-- -----------------------------------------------------------

CREATE OR REPLACE VIEW analytics.v_pipeline_health AS
WITH stage_rollup AS (
    SELECT
        psr.pipeline_run_id,
        COALESCE(
            SUM(
                GREATEST(psr.attempt - 1, 0)
            ),
            0
        ) AS retry_count
    FROM analytics.pipeline_stage_runs psr
    GROUP BY psr.pipeline_run_id
),
last_failed_stage AS (
    SELECT DISTINCT ON (psr.pipeline_run_id)
        psr.pipeline_run_id,
        psr.stage_name AS failed_stage,
        psr.error_category
    FROM analytics.pipeline_stage_runs psr
    WHERE psr.status = 'FAILED'
    ORDER BY
        psr.pipeline_run_id,
        psr.started_at DESC,
        psr.attempt DESC
)
SELECT
    pr.pipeline_run_id,
    pr.logical_run_id,
    pr.status,
    pr.started_at,
    pr.completed_at,
    pr.duration_seconds,
    pr.orders_loaded,
    pr.order_items_loaded,
    pr.analytics_rows,
    lfs.failed_stage,
    COALESCE(sr.retry_count, 0) AS retry_count,
    lfs.error_category
FROM analytics.pipeline_runs pr
LEFT JOIN stage_rollup sr
    ON sr.pipeline_run_id = pr.pipeline_run_id
LEFT JOIN last_failed_stage lfs
    ON lfs.pipeline_run_id = pr.pipeline_run_id
    -- Only surface a "failed_stage" for runs that are
    -- terminally FAILED. A stage that failed once and then
    -- succeeded on retry (pipeline status = SUCCESS) is not
    -- a health concern.
    AND pr.status = 'FAILED';

COMMIT;

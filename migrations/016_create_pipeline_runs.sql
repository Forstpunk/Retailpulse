CREATE TABLE IF NOT EXISTS analytics.pipeline_runs (
    pipeline_run_id UUID PRIMARY KEY,

    logical_run_id VARCHAR(200) NOT NULL,

    batch_id UUID,

    status VARCHAR(30) NOT NULL,

    ingestion_completed BOOLEAN NOT NULL DEFAULT FALSE,

    quality_passed BOOLEAN NOT NULL DEFAULT FALSE,

    analytics_completed BOOLEAN NOT NULL DEFAULT FALSE,

    orders_loaded BIGINT NOT NULL DEFAULT 0,

    order_items_loaded BIGINT NOT NULL DEFAULT 0,

    analytics_rows BIGINT NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL,

    completed_at TIMESTAMPTZ,

    duration_seconds NUMERIC(18,3),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_pipeline_run_status
        CHECK (
            status IN (
                'RUNNING',
                'SUCCESS',
                'FAILED'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_logical_run
    ON analytics.pipeline_runs(logical_run_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_batch
    ON analytics.pipeline_runs(batch_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON analytics.pipeline_runs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started
    ON analytics.pipeline_runs(started_at);
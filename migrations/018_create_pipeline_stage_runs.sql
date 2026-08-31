CREATE TABLE IF NOT EXISTS analytics.pipeline_stage_runs (
    stage_run_id BIGSERIAL PRIMARY KEY,

    pipeline_run_id UUID NOT NULL,

    stage_name VARCHAR(100) NOT NULL,

    status VARCHAR(30) NOT NULL,

    attempt INTEGER NOT NULL DEFAULT 1,

    started_at TIMESTAMPTZ NOT NULL,

    completed_at TIMESTAMPTZ,

    duration_ms BIGINT,

    records_processed BIGINT,

    error_category VARCHAR(50),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_stage_run_pipeline
        FOREIGN KEY (pipeline_run_id)
        REFERENCES analytics.pipeline_runs(
            pipeline_run_id
        ),

    CONSTRAINT chk_stage_run_status
        CHECK (
            status IN (
                'RUNNING',
                'SUCCESS',
                'FAILED'
            )
        ),

    CONSTRAINT chk_stage_run_attempt
        CHECK (
            attempt > 0
        ),

    CONSTRAINT chk_stage_run_duration
        CHECK (
            duration_ms IS NULL
            OR duration_ms >= 0
        ),

    CONSTRAINT chk_stage_run_records
        CHECK (
            records_processed IS NULL
            OR records_processed >= 0
        )
);

CREATE INDEX IF NOT EXISTS
    idx_pipeline_stage_runs_pipeline
ON analytics.pipeline_stage_runs(
    pipeline_run_id
);

CREATE INDEX IF NOT EXISTS
    idx_pipeline_stage_runs_stage
ON analytics.pipeline_stage_runs(
    stage_name
);

CREATE INDEX IF NOT EXISTS
    idx_pipeline_stage_runs_status
ON analytics.pipeline_stage_runs(
    status
);

CREATE INDEX IF NOT EXISTS
    idx_pipeline_stage_runs_started
ON analytics.pipeline_stage_runs(
    started_at
);
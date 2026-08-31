-- Generic incremental-processing ledger. One row per
-- (pipeline_name, source_name): the high-water mark of
-- source data that has been fully processed through
-- analytics. Advanced only after a full successful
-- extract -> load -> mart-refresh cycle (see
-- analytics.build.build_analytics).

BEGIN;

CREATE TABLE IF NOT EXISTS analytics.pipeline_watermarks (
    watermark_id BIGSERIAL PRIMARY KEY,

    pipeline_name VARCHAR(200) NOT NULL,

    source_name VARCHAR(200) NOT NULL,

    watermark_column VARCHAR(100) NOT NULL,

    watermark_value VARCHAR(200) NOT NULL,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_pipeline_watermarks_scope
        UNIQUE (pipeline_name, source_name)
);

COMMIT;

CREATE TABLE IF NOT EXISTS retail.ingestion_batches (
    batch_id UUID PRIMARY KEY,

    source_system VARCHAR(100) NOT NULL,

    batch_type VARCHAR(100) NOT NULL,

    status VARCHAR(30) NOT NULL,

    record_count INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_ingestion_batch_status
        CHECK (
            status IN (
                'STARTED',
                'COMPLETED',
                'FAILED'
            )
        ),

    CONSTRAINT chk_ingestion_batch_record_count
        CHECK (record_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_source
    ON retail.ingestion_batches(source_system);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_status
    ON retail.ingestion_batches(status);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_created_at
    ON retail.ingestion_batches(created_at);
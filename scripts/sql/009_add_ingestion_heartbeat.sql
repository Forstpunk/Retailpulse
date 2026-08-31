ALTER TABLE retail.ingestion_batches
    ADD COLUMN IF NOT EXISTS last_heartbeat_at
        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE retail.ingestion_batches
    ADD COLUMN IF NOT EXISTS max_attempts
        INTEGER NOT NULL DEFAULT 3;

ALTER TABLE retail.ingestion_batches
    ADD CONSTRAINT chk_ingestion_batch_max_attempts
        CHECK (max_attempts > 0);
ALTER TABLE retail.ingestion_batches
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER
        NOT NULL DEFAULT 1;

ALTER TABLE retail.ingestion_batches
    ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE retail.ingestion_batches
    ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE retail.ingestion_batches
    ADD CONSTRAINT chk_ingestion_batch_attempt_count
        CHECK (attempt_count > 0);
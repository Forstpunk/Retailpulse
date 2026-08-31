CREATE TABLE IF NOT EXISTS retail.ingestion_quality_results (
    quality_result_id BIGSERIAL PRIMARY KEY,

    batch_id UUID NOT NULL,

    check_name VARCHAR(200) NOT NULL,

    status VARCHAR(30) NOT NULL,

    observed_value VARCHAR(500),

    expected_value VARCHAR(500),

    message TEXT,

    checked_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_quality_results_batch
        FOREIGN KEY (batch_id)
        REFERENCES retail.ingestion_batches(batch_id),

    CONSTRAINT chk_quality_result_status
        CHECK (
            status IN ('PASS', 'FAIL')
        )
);

CREATE INDEX IF NOT EXISTS
idx_quality_results_batch
ON retail.ingestion_quality_results(batch_id);

CREATE INDEX IF NOT EXISTS
idx_quality_results_status
ON retail.ingestion_quality_results(status);

CREATE INDEX IF NOT EXISTS
idx_quality_results_checked_at
ON retail.ingestion_quality_results(checked_at);
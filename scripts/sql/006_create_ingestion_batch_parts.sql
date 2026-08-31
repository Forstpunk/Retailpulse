CREATE TABLE retail.ingestion_batch_parts (
    batch_id UUID NOT NULL,
    part_number INTEGER NOT NULL,

    status VARCHAR(30) NOT NULL,

    record_count INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ingestion_batch_parts
        PRIMARY KEY (
            batch_id,
            part_number
        ),

    CONSTRAINT fk_ingestion_batch_parts_batch
        FOREIGN KEY (batch_id)
        REFERENCES retail.ingestion_batches(batch_id),

    CONSTRAINT chk_ingestion_batch_parts_part_number
        CHECK (part_number > 0),

    CONSTRAINT chk_ingestion_batch_parts_record_count
        CHECK (record_count >= 0),

    CONSTRAINT chk_ingestion_batch_parts_status
        CHECK (
            status IN (
                'STARTED',
                'COMPLETED',
                'FAILED'
            )
        )
);

CREATE INDEX idx_ingestion_batch_parts_batch
    ON retail.ingestion_batch_parts(batch_id);

CREATE INDEX idx_ingestion_batch_parts_status
    ON retail.ingestion_batch_parts(status);
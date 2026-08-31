ALTER TABLE retail.ingestion_batch_parts
ADD COLUMN start_order_id BIGINT;

ALTER TABLE retail.ingestion_batch_parts
ADD COLUMN start_order_item_id BIGINT;

ALTER TABLE retail.ingestion_batch_parts
ADD COLUMN order_item_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE retail.ingestion_batch_parts
ADD CONSTRAINT chk_ingestion_batch_parts_start_order_id
CHECK (
    start_order_id IS NULL
    OR start_order_id > 0
);

ALTER TABLE retail.ingestion_batch_parts
ADD CONSTRAINT chk_ingestion_batch_parts_start_order_item_id
CHECK (
    start_order_item_id IS NULL
    OR start_order_item_id > 0
);

ALTER TABLE retail.ingestion_batch_parts
ADD CONSTRAINT chk_ingestion_batch_parts_order_item_count
CHECK (
    order_item_count >= 0
);
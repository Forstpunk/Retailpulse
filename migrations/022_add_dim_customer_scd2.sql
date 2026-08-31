-- SCD Type 2 versioning for analytics.dim_customer, tracking
-- customer_segment changes (a realistic business attribute:
-- customers get promoted/demoted between STANDARD/PREMIUM/VIP
-- over time, and historical analysis needs to know which
-- segment a customer was in at the time of a given order).
--
-- Other attributes (phone, city, status, ...) are NOT
-- versioned — they are overwritten in place on the current
-- row, matching how most production SCD2 dimensions mix
-- Type 1 and Type 2 behavior on the same table.

BEGIN;

ALTER TABLE analytics.dim_customer
    ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS is_current BOOLEAN;

-- Backfill existing rows as a single open version each.
UPDATE analytics.dim_customer
SET
    valid_from = source_created_at,
    valid_to = NULL,
    is_current = TRUE
WHERE valid_from IS NULL;

ALTER TABLE analytics.dim_customer
    ALTER COLUMN valid_from SET NOT NULL,
    ALTER COLUMN is_current SET NOT NULL;

ALTER TABLE analytics.dim_customer
    ADD CONSTRAINT chk_dim_customer_current_open
        CHECK (
            (is_current AND valid_to IS NULL)
            OR
            (NOT is_current AND valid_to IS NOT NULL)
        );

-- customer_id and customer_number were previously unique
-- across the whole table. Under SCD2 the same customer_id
-- (and customer_number, a stable per-customer attribute)
-- can legitimately appear on multiple historical rows, so
-- uniqueness is now scoped to the current version only.

ALTER TABLE analytics.dim_customer
    DROP CONSTRAINT dim_customer_customer_id_key;

ALTER TABLE analytics.dim_customer
    DROP CONSTRAINT uq_dim_customer_number;

CREATE INDEX IF NOT EXISTS
    idx_dim_customer_customer_id
ON analytics.dim_customer(customer_id);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_dim_customer_current_id
ON analytics.dim_customer(customer_id)
WHERE is_current;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_dim_customer_current_number
ON analytics.dim_customer(customer_number)
WHERE is_current;

CREATE INDEX IF NOT EXISTS
    idx_dim_customer_valid_range
ON analytics.dim_customer(customer_id, valid_from, valid_to);

COMMIT;

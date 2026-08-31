CREATE TABLE IF NOT EXISTS analytics.fact_order (
    order_key           BIGSERIAL PRIMARY KEY,

    order_id            BIGINT NOT NULL UNIQUE,

    customer_key        BIGINT NOT NULL,
    store_key           BIGINT,
    order_date_key      INTEGER NOT NULL,

    order_channel       VARCHAR(30) NOT NULL,
    order_status        VARCHAR(30) NOT NULL,
    currency_code       CHAR(3) NOT NULL,

    subtotal_amount     NUMERIC(14,2) NOT NULL,
    discount_amount     NUMERIC(14,2) NOT NULL,
    tax_amount          NUMERIC(14,2) NOT NULL,
    shipping_amount     NUMERIC(14,2) NOT NULL,
    total_amount        NUMERIC(14,2) NOT NULL,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_order_customer
        FOREIGN KEY (customer_key)
        REFERENCES analytics.dim_customer(customer_key),

    CONSTRAINT fk_fact_order_store
        FOREIGN KEY (store_key)
        REFERENCES analytics.dim_store(store_key),

    CONSTRAINT fk_fact_order_date
        FOREIGN KEY (order_date_key)
        REFERENCES analytics.dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_order_customer
    ON analytics.fact_order(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_store
    ON analytics.fact_order(store_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_date
    ON analytics.fact_order(order_date_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_status
    ON analytics.fact_order(order_status);

CREATE INDEX IF NOT EXISTS idx_fact_order_channel
    ON analytics.fact_order(order_channel);
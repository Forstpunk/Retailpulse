CREATE TABLE IF NOT EXISTS analytics.mart_store_performance (
    store_key           BIGINT PRIMARY KEY,

    store_id            BIGINT NOT NULL,
    store_code          VARCHAR(30) NOT NULL,
    store_name          VARCHAR(200) NOT NULL,

    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(100) NOT NULL,
    country_code        CHAR(2) NOT NULL,
    region              VARCHAR(100) NOT NULL,
    store_type          VARCHAR(50) NOT NULL,

    order_count         BIGINT NOT NULL,
    units_sold          BIGINT NOT NULL,

    gross_sales         NUMERIC(18,2) NOT NULL,
    discount_amount     NUMERIC(18,2) NOT NULL,
    tax_amount          NUMERIC(18,2) NOT NULL,
    net_sales           NUMERIC(18,2) NOT NULL,

    average_order_value NUMERIC(18,2) NOT NULL,

    first_order_date    DATE,
    last_order_date     DATE,

    store_rank          BIGINT,

    refreshed_at        TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mart_store_store_id
    ON analytics.mart_store_performance(store_id);

CREATE INDEX IF NOT EXISTS idx_mart_store_region
    ON analytics.mart_store_performance(region);

CREATE INDEX IF NOT EXISTS idx_mart_store_type
    ON analytics.mart_store_performance(store_type);

CREATE INDEX IF NOT EXISTS idx_mart_store_net_sales
    ON analytics.mart_store_performance(net_sales);

CREATE INDEX IF NOT EXISTS idx_mart_store_rank
    ON analytics.mart_store_performance(store_rank);
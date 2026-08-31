CREATE TABLE IF NOT EXISTS analytics.mart_daily_sales (
    date_key            INTEGER PRIMARY KEY,

    order_count         BIGINT NOT NULL,
    order_item_count    BIGINT NOT NULL,

    units_sold          BIGINT NOT NULL,

    gross_sales         NUMERIC(18,2) NOT NULL,
    discount_amount     NUMERIC(18,2) NOT NULL,
    tax_amount          NUMERIC(18,2) NOT NULL,
    shipping_amount     NUMERIC(18,2) NOT NULL,

    net_sales           NUMERIC(18,2) NOT NULL,

    average_order_value NUMERIC(18,2) NOT NULL,

    refreshed_at        TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_daily_sales_date
        FOREIGN KEY (date_key)
        REFERENCES analytics.dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_mart_daily_sales_date
    ON analytics.mart_daily_sales(date_key);
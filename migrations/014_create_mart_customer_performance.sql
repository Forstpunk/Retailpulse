CREATE TABLE IF NOT EXISTS analytics.mart_customer_performance (
    customer_key        BIGINT PRIMARY KEY,

    customer_id         BIGINT NOT NULL,
    customer_number     VARCHAR(30) NOT NULL,

    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,

    customer_segment    VARCHAR(50) NOT NULL,
    city                VARCHAR(100),
    state               VARCHAR(100),
    country_code        CHAR(2),

    order_count         BIGINT NOT NULL,
    units_purchased     BIGINT NOT NULL,

    gross_sales         NUMERIC(18,2) NOT NULL,
    discount_amount     NUMERIC(18,2) NOT NULL,
    tax_amount          NUMERIC(18,2) NOT NULL,
    net_sales           NUMERIC(18,2) NOT NULL,

    average_order_value NUMERIC(18,2) NOT NULL,

    first_order_date    TIMESTAMPTZ,
    last_order_date     TIMESTAMPTZ,

    customer_rank       BIGINT,

    refreshed_at        TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mart_customer_customer_id
    ON analytics.mart_customer_performance(customer_id);

CREATE INDEX IF NOT EXISTS idx_mart_customer_segment
    ON analytics.mart_customer_performance(customer_segment);

CREATE INDEX IF NOT EXISTS idx_mart_customer_net_sales
    ON analytics.mart_customer_performance(net_sales);

CREATE INDEX IF NOT EXISTS idx_mart_customer_rank
    ON analytics.mart_customer_performance(customer_rank);
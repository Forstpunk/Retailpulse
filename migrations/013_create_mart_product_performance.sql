CREATE TABLE IF NOT EXISTS analytics.mart_product_performance (
    product_key          BIGINT PRIMARY KEY,

    product_id           BIGINT NOT NULL,
    sku                  VARCHAR(50) NOT NULL,
    product_name         VARCHAR(255) NOT NULL,

    category_key         BIGINT,
    supplier_key         BIGINT,

    order_count          BIGINT NOT NULL,
    units_sold           BIGINT NOT NULL,

    gross_sales          NUMERIC(18,2) NOT NULL,
    discount_amount      NUMERIC(18,2) NOT NULL,
    tax_amount           NUMERIC(18,2) NOT NULL,

    net_sales            NUMERIC(18,2) NOT NULL,

    average_unit_price   NUMERIC(18,2) NOT NULL,

    discount_rate        NUMERIC(10,4) NOT NULL,

    sales_rank           BIGINT,

    refreshed_at         TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mart_product
        FOREIGN KEY (product_key)
        REFERENCES analytics.dim_product(product_key)
);

CREATE INDEX IF NOT EXISTS idx_mart_product_product_id
    ON analytics.mart_product_performance(product_id);

CREATE INDEX IF NOT EXISTS idx_mart_product_category
    ON analytics.mart_product_performance(category_key);

CREATE INDEX IF NOT EXISTS idx_mart_product_sales_rank
    ON analytics.mart_product_performance(sales_rank);

CREATE INDEX IF NOT EXISTS idx_mart_product_net_sales
    ON analytics.mart_product_performance(net_sales);
CREATE TABLE IF NOT EXISTS analytics.fact_order_item (
    order_item_key      BIGSERIAL PRIMARY KEY,

    order_item_id       BIGINT NOT NULL UNIQUE,

    order_key           BIGINT NOT NULL,
    product_key         BIGINT NOT NULL,

    quantity            INTEGER NOT NULL,

    unit_price          NUMERIC(12,2) NOT NULL,
    discount_amount     NUMERIC(12,2) NOT NULL,
    tax_amount          NUMERIC(12,2) NOT NULL,
    line_total          NUMERIC(14,2) NOT NULL,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_order_item_order
        FOREIGN KEY (order_key)
        REFERENCES analytics.fact_order(order_key),

    CONSTRAINT fk_fact_order_item_product
        FOREIGN KEY (product_key)
        REFERENCES analytics.dim_product(product_key),

    CONSTRAINT chk_fact_order_item_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_fact_order_item_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_fact_order_item_discount
        CHECK (discount_amount >= 0),

    CONSTRAINT chk_fact_order_item_tax
        CHECK (tax_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_fact_order_item_order
    ON analytics.fact_order_item(order_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_item_product
    ON analytics.fact_order_item(product_key);

CREATE INDEX IF NOT EXISTS idx_fact_order_item_updated
    ON analytics.fact_order_item(source_updated_at);
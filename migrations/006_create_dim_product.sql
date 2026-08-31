CREATE TABLE IF NOT EXISTS analytics.dim_product (
    product_key         BIGSERIAL PRIMARY KEY,

    product_id          BIGINT NOT NULL UNIQUE,
    sku                 VARCHAR(50) NOT NULL,
    product_name        VARCHAR(255) NOT NULL,

    category_id         BIGINT NOT NULL,
    supplier_id         BIGINT,

    unit_price          NUMERIC(12,2) NOT NULL,
    cost_price          NUMERIC(12,2) NOT NULL,
    status              VARCHAR(30) NOT NULL,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dim_product_sku
        UNIQUE (sku)
);

CREATE INDEX IF NOT EXISTS idx_dim_product_category
    ON analytics.dim_product(category_id);

CREATE INDEX IF NOT EXISTS idx_dim_product_supplier
    ON analytics.dim_product(supplier_id);

CREATE INDEX IF NOT EXISTS idx_dim_product_updated
    ON analytics.dim_product(source_updated_at);
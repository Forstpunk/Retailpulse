CREATE TABLE IF NOT EXISTS analytics.dim_category (
    category_key        BIGSERIAL PRIMARY KEY,

    category_id         BIGINT NOT NULL UNIQUE,
    category_name       VARCHAR(100) NOT NULL,
    parent_category_id  BIGINT,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_category_parent
    ON analytics.dim_category(parent_category_id);

CREATE INDEX IF NOT EXISTS idx_dim_category_updated
    ON analytics.dim_category(source_updated_at);
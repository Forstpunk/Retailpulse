CREATE TABLE IF NOT EXISTS analytics.dim_store (
    store_key           BIGSERIAL PRIMARY KEY,

    store_id            BIGINT NOT NULL UNIQUE,
    store_code          VARCHAR(30) NOT NULL,

    store_name          VARCHAR(200) NOT NULL,

    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(100) NOT NULL,
    country_code        CHAR(2) NOT NULL,
    region              VARCHAR(100) NOT NULL,

    store_type          VARCHAR(50) NOT NULL,
    opened_date         DATE NOT NULL,
    status              VARCHAR(30) NOT NULL,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dim_store_code
        UNIQUE (store_code)
);

CREATE INDEX IF NOT EXISTS idx_dim_store_region
    ON analytics.dim_store(region);

CREATE INDEX IF NOT EXISTS idx_dim_store_type
    ON analytics.dim_store(store_type);

CREATE INDEX IF NOT EXISTS idx_dim_store_status
    ON analytics.dim_store(status);

CREATE INDEX IF NOT EXISTS idx_dim_store_updated
    ON analytics.dim_store(source_updated_at);
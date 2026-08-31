CREATE SCHEMA IF NOT EXISTS analytics;

CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS analytics.dim_supplier (
    supplier_key       BIGSERIAL PRIMARY KEY,

    supplier_id        BIGINT NOT NULL UNIQUE,
    supplier_name      VARCHAR(200) NOT NULL,

    country_code       CHAR(2) NOT NULL,
    status             VARCHAR(30) NOT NULL,

    source_created_at  TIMESTAMPTZ NOT NULL,
    source_updated_at  TIMESTAMPTZ NOT NULL,

    created_at         TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at         TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);
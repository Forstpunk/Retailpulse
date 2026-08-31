CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_key        BIGSERIAL PRIMARY KEY,

    customer_id         BIGINT NOT NULL UNIQUE,
    customer_number     VARCHAR(30) NOT NULL,

    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL,
    phone               VARCHAR(30),

    city                VARCHAR(100),
    state               VARCHAR(100),
    country_code        CHAR(2),

    customer_segment    VARCHAR(50) NOT NULL,
    date_of_birth       DATE,
    status              VARCHAR(30) NOT NULL,

    source_created_at   TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at          TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dim_customer_number
        UNIQUE (customer_number)
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_email
    ON analytics.dim_customer(email);

CREATE INDEX IF NOT EXISTS idx_dim_customer_segment
    ON analytics.dim_customer(customer_segment);

CREATE INDEX IF NOT EXISTS idx_dim_customer_updated
    ON analytics.dim_customer(source_updated_at);
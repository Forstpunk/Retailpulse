CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key            INTEGER PRIMARY KEY,

    full_date           DATE NOT NULL UNIQUE,

    day_of_month        SMALLINT NOT NULL,
    day_of_week         SMALLINT NOT NULL,
    day_name            VARCHAR(20) NOT NULL,

    week_of_year        SMALLINT NOT NULL,

    month_number        SMALLINT NOT NULL,
    month_name          VARCHAR(20) NOT NULL,

    quarter_number      SMALLINT NOT NULL,

    year_number         SMALLINT NOT NULL,

    is_weekend          BOOLEAN NOT NULL
);
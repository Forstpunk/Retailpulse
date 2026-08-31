from collections.abc import Iterable

from psycopg import Connection

from retailpulse.analytics.models.customer import (
    SourceCustomer,
)


def load_customers(
    connection: Connection,
    customers: Iterable[SourceCustomer],
) -> int:
    """
    Load source customers into analytics.dim_customer as
    a Type 2 slowly changing dimension on customer_segment:
    a segment change closes the current version
    (is_current = FALSE, valid_to set) and opens a new one,
    so historical queries can see which segment a customer
    was in as of any past date. All other attributes
    (phone, city, status, ...) are overwritten in place on
    the current version — only segment changes are
    versioned.

    Rows are staged via COPY and resolved with set-based
    SQL rather than one round trip per customer — see
    order_fact_loader for why that matters at RetailPulse's
    data volumes.

    Returns
    -------
    int
        Number of customers processed.
    """

    customers = list(customers)

    if not customers:
        return 0

    with connection.transaction(), connection.cursor() as cursor:

        cursor.execute(
            """
                CREATE TEMP TABLE IF NOT EXISTS
                    tmp_dim_customer_staging (
                        customer_id BIGINT,
                        customer_number VARCHAR(30),
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        email VARCHAR(255),
                        phone VARCHAR(30),
                        city VARCHAR(100),
                        state VARCHAR(100),
                        country_code CHAR(2),
                        customer_segment VARCHAR(50),
                        date_of_birth DATE,
                        status VARCHAR(30),
                        source_created_at TIMESTAMPTZ,
                        source_updated_at TIMESTAMPTZ
                    )
                ON COMMIT DROP
                """
        )

        cursor.execute(
            "TRUNCATE TABLE tmp_dim_customer_staging"
        )

        with cursor.copy(
            """
                COPY tmp_dim_customer_staging (
                    customer_id,
                    customer_number,
                    first_name,
                    last_name,
                    email,
                    phone,
                    city,
                    state,
                    country_code,
                    customer_segment,
                    date_of_birth,
                    status,
                    source_created_at,
                    source_updated_at
                )
                FROM STDIN
                """
        ) as copy:

            for customer in customers:

                copy.write_row(
                    (
                        customer.customer_id,
                        customer.customer_number,
                        customer.first_name,
                        customer.last_name,
                        customer.email,
                        customer.phone,
                        customer.city,
                        customer.state,
                        customer.country_code,
                        customer.customer_segment,
                        customer.date_of_birth,
                        customer.status,
                        customer.created_at,
                        customer.updated_at,
                    )
                )

        # -------------------------------------------------
        # 1. Close the current version of every customer
        #    whose segment changed.
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE analytics.dim_customer dc
                SET
                    is_current = FALSE,
                    valid_to = s.source_updated_at,
                    updated_at = CURRENT_TIMESTAMP
                FROM tmp_dim_customer_staging s
                WHERE dc.customer_id = s.customer_id
                  AND dc.is_current = TRUE
                  AND dc.customer_segment
                      != s.customer_segment
                  AND dc.source_updated_at
                      < s.source_updated_at
                """
        )

        # -------------------------------------------------
        # 2. Open a new current version for every customer
        #    that has no current row: brand-new customers,
        #    and customers just closed by step 1.
        # -------------------------------------------------

        cursor.execute(
            """
                INSERT INTO analytics.dim_customer (
                    customer_id,
                    customer_number,
                    first_name,
                    last_name,
                    email,
                    phone,
                    city,
                    state,
                    country_code,
                    customer_segment,
                    date_of_birth,
                    status,
                    source_created_at,
                    source_updated_at,
                    valid_from,
                    valid_to,
                    is_current
                )
                SELECT
                    s.customer_id,
                    s.customer_number,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.phone,
                    s.city,
                    s.state,
                    s.country_code,
                    s.customer_segment,
                    s.date_of_birth,
                    s.status,
                    s.source_created_at,
                    s.source_updated_at,
                    s.source_updated_at,
                    NULL,
                    TRUE
                FROM tmp_dim_customer_staging s
                LEFT JOIN analytics.dim_customer dc
                    ON dc.customer_id = s.customer_id
                    AND dc.is_current = TRUE
                WHERE dc.customer_key IS NULL
                """
        )

        # -------------------------------------------------
        # 3. In-place update of non-segment attributes for
        #    customers whose segment did NOT change.
        # -------------------------------------------------

        cursor.execute(
            """
                UPDATE analytics.dim_customer dc
                SET
                    customer_number =
                        s.customer_number,
                    first_name =
                        s.first_name,
                    last_name =
                        s.last_name,
                    email =
                        s.email,
                    phone =
                        s.phone,
                    city =
                        s.city,
                    state =
                        s.state,
                    country_code =
                        s.country_code,
                    date_of_birth =
                        s.date_of_birth,
                    status =
                        s.status,
                    source_updated_at =
                        s.source_updated_at,
                    updated_at =
                        CURRENT_TIMESTAMP
                FROM tmp_dim_customer_staging s
                WHERE dc.customer_id = s.customer_id
                  AND dc.is_current = TRUE
                  AND dc.customer_segment
                      = s.customer_segment
                  AND dc.source_updated_at
                      < s.source_updated_at
                """
        )

    return len(customers)

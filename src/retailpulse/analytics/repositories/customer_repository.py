from psycopg import Connection

from retailpulse.analytics.models.customer import (
    SourceCustomer,
)


def get_customers(
    connection: Connection,
) -> list[SourceCustomer]:
    """
    Read customers from the retail source schema.

    This repository is read-only.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                customer_id,
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
                created_at,
                updated_at,
                customer_number
            FROM retail.customers
            ORDER BY customer_id
            """
        )

        rows = cursor.fetchall()

    return [
        SourceCustomer(
            customer_id=row[0],
            first_name=row[1],
            last_name=row[2],
            email=row[3],
            phone=row[4],
            city=row[5],
            state=row[6],
            country_code=row[7],
            customer_segment=row[8],
            date_of_birth=row[9],
            status=row[10],
            created_at=row[11],
            updated_at=row[12],
            customer_number=row[13],
        )
        for row in rows
    ]
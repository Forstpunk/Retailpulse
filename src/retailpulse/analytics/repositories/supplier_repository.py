from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection


@dataclass(frozen=True)
class SourceSupplier:
    supplier_id: int
    supplier_name: str
    country_code: str
    status: str
    created_at: datetime
    updated_at: datetime


def get_suppliers(
    connection: Connection,
) -> list[SourceSupplier]:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                supplier_id,
                supplier_name,
                country_code,
                status,
                created_at,
                updated_at
            FROM retail.suppliers
            ORDER BY supplier_id
            """
        )

        rows = cursor.fetchall()

    return [
        SourceSupplier(
            supplier_id=row[0],
            supplier_name=row[1],
            country_code=row[2],
            status=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
        for row in rows
    ]
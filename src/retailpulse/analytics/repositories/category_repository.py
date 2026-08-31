from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection


@dataclass(frozen=True)
class SourceCategory:
    category_id: int
    category_name: str
    parent_category_id: int | None
    created_at: datetime
    updated_at: datetime


def get_categories(
    connection: Connection,
) -> list[SourceCategory]:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                category_id,
                category_name,
                parent_category_id,
                created_at,
                updated_at
            FROM retail.categories
            ORDER BY category_id
            """
        )

        rows = cursor.fetchall()

    return [
        SourceCategory(
            category_id=row[0],
            category_name=row[1],
            parent_category_id=row[2],
            created_at=row[3],
            updated_at=row[4],
        )
        for row in rows
    ]
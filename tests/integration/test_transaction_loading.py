from retailpulse.common.database import (
    get_connection,
)
from retailpulse.generators.repositories import (
    get_next_order_id,
    get_next_order_item_id,
)


def test_database_connection():
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1"
        )

        result = cursor.fetchone()

    assert result == (1,)


def test_next_order_id():
    with get_connection() as connection:
        next_id = get_next_order_id(
            connection
        )

    assert next_id >= 1


def test_next_order_item_id():
    with get_connection() as connection:
        next_id = get_next_order_item_id(
            connection
        )

    assert next_id >= 1
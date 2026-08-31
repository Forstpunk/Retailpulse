from collections.abc import Iterable
from uuid import UUID

from psycopg import Connection

from retailpulse.generators.ingestion_parts_repository import (
    complete_batch_part,
)
from retailpulse.generators.ingestion_repository import (
    complete_batch,
)
from retailpulse.generators.transaction_loader import (
    load_transaction_batch,
)
from retailpulse.generators.transactions import (
    OrderTransaction,
)


def process_transaction_batch(
    connection: Connection,
    *,
    batch_id: UUID,
    part_number: int,
    transactions: Iterable[OrderTransaction],
) -> tuple[int, int]:
    """
    Process one physical transaction batch.

    Transaction boundaries:

        1. load_transaction_batch()
           owns the orders/order_items transaction.

        2. complete_batch_part()
           commits the physical checkpoint.

    A successful physical batch therefore becomes
    durable before the next physical batch starts.
    """

    orders_loaded, order_items_loaded = (
        load_transaction_batch(
            connection,
            transactions,
        )
    )

    complete_batch_part(
        connection,
        batch_id=batch_id,
        part_number=part_number,
        record_count=orders_loaded,
        order_item_count=order_items_loaded,
    )

    connection.commit()

    return (
        orders_loaded,
        order_items_loaded,
    )


def complete_transaction_ingestion(
    connection: Connection,
    *,
    batch_id: UUID,
    record_count: int,
) -> None:
    """
    Mark the logical transaction ingestion as COMPLETED.

    Called only after every physical batch has
    completed successfully.
    """

    complete_batch(
        connection,
        batch_id,
        record_count,
    )
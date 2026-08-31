from datetime import UTC, datetime
from uuid import UUID

from psycopg import Connection

from retailpulse.generators.batch_identity import (
    build_batch_id,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.generators.ingestion_parts_repository import (
    fail_batch_part,
    get_batch_part_start_ids,
    get_completed_batch_parts,
    start_batch_part,
)
from retailpulse.generators.ingestion_repository import (
    fail_batch,
    get_batch,
    heartbeat_batch,
    retry_failed_batch,
    start_batch,
)
from retailpulse.generators.repositories import (
    get_customer_ids,
    get_next_order_id,
    get_next_order_item_id,
    get_product_prices,
    get_store_ids,
)
from retailpulse.generators.transaction_pipeline import (
    complete_transaction_ingestion,
    process_transaction_batch,
)
from retailpulse.generators.transaction_resume import (
    calculate_order_item_offset,
    generate_transaction_slice,
)
from retailpulse.pipeline.errors import (
    DataQualityError,
)
from retailpulse.quality.pipeline import (
    run_and_persist_transaction_quality,
)
from retailpulse.quality.reconciliation import (
    reconcile_transaction_batch,
)

SOURCE_SYSTEM = "retailpulse_generator"

BATCH_TYPE = "ORDER_TRANSACTION"


def run_transaction_ingestion(
    connection: Connection,
    config: GeneratorConfig,
    *,
    logical_run_id: str,
    fail_part: int | None = None,
    pipeline_run_id: UUID | None = None,
) -> dict[str, int | str | float]:
    """
    Generate and load one logical transaction batch.

    A logical ingestion batch may consist of multiple
    physical batches.

    Each physical batch is independently checkpointed so
    completed physical batches can be skipped during retry.

    A retry reuses the original source IDs recorded by
    physical batch 1. This guarantees deterministic
    transaction generation across retries.

    Processing flow
    ---------------
    1. Build deterministic logical batch ID.
    2. Claim the logical ingestion batch.
    3. Resume a FAILED batch when necessary.
    4. Load transaction reference state.
    5. Determine deterministic source IDs.
    6. Load existing physical checkpoints.
    7. Generate and process physical batches.
    8. Validate logical record counts.
    9. Reconcile PostgreSQL state.
    10. Run and persist quality checks.
    11. Complete the logical ingestion batch.
    12. Report ingestion metrics.
    """

    # =========================================================
    # 0. Validate failure injection
    # =========================================================

    if fail_part is not None and fail_part <= 0:
        raise ValueError(
            "fail_part must be greater than zero"
        )

    # =========================================================
    # 1. Build deterministic logical batch identity
    # =========================================================

    batch_id = build_batch_id(
        source_system=SOURCE_SYSTEM,
        batch_type=BATCH_TYPE,
        logical_run_id=logical_run_id,
    )

    print()
    print(
        f"Transaction batch ID: {batch_id}"
    )

    # =========================================================
    # 2. Claim logical ingestion batch
    # =========================================================

    claimed = start_batch(
        connection,
        batch_id,
        SOURCE_SYSTEM,
        BATCH_TYPE,
    )

    if not claimed:

        existing_batch = get_batch(
            connection,
            batch_id,
        )

        if existing_batch is None:
            raise RuntimeError(
                "Batch could not be claimed and "
                "could not be found."
            )

        # -----------------------------------------------------
        # Already completed
        # -----------------------------------------------------

        if existing_batch.status == "COMPLETED":

            print()
            print(
                "Transaction batch already "
                "completed."
            )

            print(
                f"Skipping batch: {batch_id}"
            )

            return {
                "batch_id": str(batch_id),
                "orders": existing_batch.record_count,
                "order_items": 0,
                "transaction_batches": 0,
                "skipped": 1,
                "duration_seconds": 0.0,
                "orders_per_second": 0.0,
            }

        # -----------------------------------------------------
        # Existing batch must be FAILED to retry
        # -----------------------------------------------------

        if existing_batch.status != "FAILED":
            raise RuntimeError(
                f"Batch {batch_id} already exists "
                f"with unexpected status: "
                f"{existing_batch.status}"
            )

        retried = retry_failed_batch(
            connection,
            batch_id,
        )

        if not retried:
            raise RuntimeError(
                f"Batch {batch_id} has exhausted "
                "its retry attempts."
            )

        print()
        print(
            "Existing FAILED batch "
            "successfully claimed for retry."
        )

    else:

        print(
            "Transaction batch claimed successfully."
        )

    # =========================================================
    # 3. Start timer
    # =========================================================

    started_at = datetime.now(
        UTC,
    )

    try:

        # =====================================================
        # 4. Read transaction reference state
        # =====================================================

        print()
        print(
            "Preparing transaction "
            "reference state..."
        )

        customer_ids = get_customer_ids(
            connection,
        )

        store_ids = get_store_ids(
            connection,
        )

        product_prices = get_product_prices(
            connection,
        )

        if not customer_ids:
            raise RuntimeError(
                "No customers available"
            )

        if not store_ids:
            raise RuntimeError(
                "No stores available"
            )

        if not product_prices:
            raise RuntimeError(
                "No products available"
            )

        print(
            f"Available customers: "
            f"{len(customer_ids):,}"
        )

        print(
            f"Available stores: "
            f"{len(store_ids):,}"
        )

        print(
            f"Available products: "
            f"{len(product_prices):,}"
        )

        # =====================================================
        # 5. Determine source IDs
        # =====================================================

        # New logical batch:
        #
        #     PostgreSQL allocates fresh IDs.
        #
        # Existing logical batch:
        #
        #     Reuse the IDs stored by physical part 1.
        #
        # This is critical for deterministic recovery.

        existing_part_start_ids = (
            get_batch_part_start_ids(
                connection,
                batch_id=batch_id,
            )
        )

        if existing_part_start_ids is None:

            start_order_id = get_next_order_id(
                connection,
            )

            start_order_item_id = (
                get_next_order_item_id(
                    connection,
                )
            )

            print()
            print(
                "New logical batch."
            )

        else:

            (
                start_order_id,
                start_order_item_id,
            ) = existing_part_start_ids

            print()
            print(
                "Resuming existing logical batch."
            )

        print(
            f"Starting order_id: "
            f"{start_order_id:,}"
        )

        print(
            f"Starting order_item_id: "
            f"{start_order_item_id:,}"
        )

        # =====================================================
        # 6. Read physical checkpoint state
        # =====================================================

        completed_parts = (
            get_completed_batch_parts(
                connection,
                batch_id=batch_id,
            )
        )

        orders_loaded = sum(
            part["orders"]
            for part in completed_parts.values()
        )

        order_items_loaded = sum(
            part["order_items"]
            for part in completed_parts.values()
        )

        transaction_batches_loaded = len(
            completed_parts
        )

        if completed_parts:

            print()
            print(
                "Existing physical "
                "checkpoints:"
            )

            for (
                part_number,
                part_data,
            ) in sorted(
                completed_parts.items()
            ):

                print(
                    f"  Part {part_number}: "
                    f"{part_data['orders']:,} "
                    "orders, "
                    f"{part_data['order_items']:,} "
                    "order items"
                )

        # =====================================================
        # 7. Determine physical batch count
        # =====================================================

        if config.orders <= 0:
            raise ValueError(
                "config.orders must be greater than zero"
            )

        if config.batch_size <= 0:
            raise ValueError(
                "config.batch_size must be greater than zero"
            )

        total_physical_batches = (
            config.orders
            + config.batch_size
            - 1
        ) // config.batch_size

        print()
        print(
            f"Total physical batches: "
            f"{total_physical_batches}"
        )

        # =====================================================
        # 8. Physical batch processing
        # =====================================================

        for part_number in range(
            1,
            total_physical_batches + 1,
        ):

            # -------------------------------------------------
            # Calculate physical batch offset
            # -------------------------------------------------

            part_offset = (
                part_number - 1
            ) * config.batch_size

            remaining_orders = (
                config.orders
                - part_offset
            )

            current_batch_size = min(
                config.batch_size,
                remaining_orders,
            )

            # -------------------------------------------------
            # Calculate order start
            # -------------------------------------------------

            current_order_id = (
                start_order_id
                + part_offset
            )

            # -------------------------------------------------
            # Calculate order-item start
            #
            # Because order-item IDs depend on the generated
            # number of items in previous orders, reproduce
            # the deterministic stream up to this offset.
            # -------------------------------------------------

            current_order_item_id = (
                calculate_order_item_offset(
                    start_order_id=start_order_id,
                    start_order_item_id=(
                        start_order_item_id
                    ),
                    start_offset=part_offset,
                    customer_ids=customer_ids,
                    store_ids=store_ids,
                    product_prices=product_prices,
                    seed=config.seed,
                    start_date=config.start_date,
                    end_date=config.end_date,
                )
            )

            print()
            print(
                f"Processing physical batch "
                f"{part_number}/"
                f"{total_physical_batches}..."
            )

            print(
                f"  Orders: "
                f"{current_batch_size:,}"
            )

            print(
                f"  Starting order_id: "
                f"{current_order_id:,}"
            )

            print(
                f"  Starting order_item_id: "
                f"{current_order_item_id:,}"
            )

            # -------------------------------------------------
            # Register physical checkpoint
            #
            # If the part is already COMPLETED, this returns
            # False and the physical batch is skipped.
            # -------------------------------------------------

            should_process = start_batch_part(
                connection,
                batch_id=batch_id,
                part_number=part_number,
                start_order_id=current_order_id,
                start_order_item_id=(
                    current_order_item_id
                ),
            )

            if not should_process:

                print(
                    f"Physical batch "
                    f"{part_number} already "
                    "completed. Skipping."
                )

                continue

            try:

                # -------------------------------------------------
                # Optional deterministic failure injection
                # -------------------------------------------------

                if fail_part == part_number:

                    raise RuntimeError(
                        f"Intentional failure injected "
                        f"for physical batch "
                        f"{part_number}"
                    )

                # -------------------------------------------------
                # Generate only this physical batch
                # -------------------------------------------------

                transaction_generator = (
                    generate_transaction_slice(
                        start_order_id=start_order_id,
                        start_order_item_id=(
                            start_order_item_id
                        ),
                        start_offset=part_offset,
                        count=current_batch_size,
                        customer_ids=customer_ids,
                        store_ids=store_ids,
                        product_prices=product_prices,
                        seed=config.seed,
                        start_date=config.start_date,
                        end_date=config.end_date,
                    )
                )

                transaction_batch = list(
                    transaction_generator
                )

                if len(transaction_batch) != (
                    current_batch_size
                ):

                    raise RuntimeError(
                        "Generated transaction "
                        "count does not match "
                        "physical batch size: "
                        f"expected="
                        f"{current_batch_size}, "
                        f"actual="
                        f"{len(transaction_batch)}"
                    )

                # -------------------------------------------------
                # Load physical batch
                #
                # process_transaction_batch() atomically
                # performs:
                #
                #   COPY orders
                #   COPY order_items
                #   COMPLETE physical checkpoint
                #
                # If any step fails, all three are rolled back.
                # -------------------------------------------------

                (
                    batch_orders,
                    batch_order_items,
                ) = process_transaction_batch(
                    connection,
                    batch_id=batch_id,
                    part_number=part_number,
                    transactions=transaction_batch,
                )

                orders_loaded += batch_orders

                order_items_loaded += (
                    batch_order_items
                )

                transaction_batches_loaded += 1

                heartbeat_batch(
                    connection,
                    batch_id,
                )

                print(
                    f"Physical batch "
                    f"{part_number} completed: "
                    f"{batch_orders:,} orders, "
                    f"{batch_order_items:,} "
                    "order items"
                )

            except Exception as exc:

                # -------------------------------------------------
                # Persist physical-part failure.
                #
                # process_transaction_batch() rolls back the
                # physical data/checkpoint transaction first.
                #
                # fail_batch_part() then records FAILED in a
                # separate transaction so the checkpoint survives.
                # -------------------------------------------------

                fail_batch_part(
                    connection,
                    batch_id=batch_id,
                    part_number=part_number,
                    error_message=str(exc),
                )

                raise

        # =====================================================
        # 9. Validate complete logical batch
        # =====================================================

        if orders_loaded != config.orders:

            raise RuntimeError(
                "Order load count does not match "
                "configured count: "
                f"expected={config.orders}, "
                f"actual={orders_loaded}"
            )

        # =====================================================
        # 10. Reconcile PostgreSQL state
        # =====================================================

        print()
        print(
            "Reconciling transaction ingestion..."
        )

        reconciliation = (
            reconcile_transaction_batch(
                connection,
                batch_id=batch_id,
                start_order_id=start_order_id,
                expected_orders=orders_loaded,
                expected_order_items=(
                    order_items_loaded
                ),
            )
        )

        print(
            f"  Expected orders: "
            f"{reconciliation.expected_orders:,}"
        )

        print(
            f"  Actual orders: "
            f"{reconciliation.actual_orders:,}"
        )

        print(
            f"  Expected order items: "
            f"{reconciliation.expected_order_items:,}"
        )

        print(
            f"  Actual order items: "
            f"{reconciliation.actual_order_items:,}"
        )

        print(
            f"  Duplicate order IDs: "
            f"{reconciliation.duplicate_order_ids:,}"
        )

        print(
            f"  Duplicate order item IDs: "
            f"{reconciliation.duplicate_order_item_ids:,}"
        )

        print(
            f"  Orphan order items: "
            f"{reconciliation.orphan_order_items:,}"
        )

        print(
            f"  Financial mismatches: "
            f"{reconciliation.order_financial_mismatches:,}"
        )

        if not reconciliation.passed:

            raise DataQualityError(
                "Transaction reconciliation failed"
            )

        # =====================================================
        # 11. Run and persist quality checks
        # =====================================================

        print()
        print(
            "Running transaction quality checks..."
        )

        quality_passed = (
            run_and_persist_transaction_quality(
                connection,
                batch_id=batch_id,
                start_order_id=start_order_id,
                expected_order_count=orders_loaded,
                expected_order_item_count=(
                    order_items_loaded
                ),
                pipeline_run_id=pipeline_run_id,
            )
        )

        if not quality_passed:

            raise DataQualityError(
                "Transaction quality checks failed"
            )

        print(
            "Transaction quality checks passed."
        )

        # =====================================================
        # 12. Complete logical ingestion
        # =====================================================

        complete_transaction_ingestion(
            connection,
            batch_id=batch_id,
            record_count=orders_loaded,
        )

    except Exception as exc:

        print()
        print(
            f"Transaction batch failed: "
            f"{batch_id}"
        )

        # Make absolutely sure the connection is not left
        # inside an aborted PostgreSQL transaction before
        # recording the logical FAILED state.

        connection.rollback()

        fail_batch(
            connection,
            batch_id,
            str(exc),
        )

        raise

    # =========================================================
    # 13. Stop timer
    # =========================================================

    completed_at = datetime.now(
        UTC,
    )

    duration_seconds = (
        completed_at - started_at
    ).total_seconds()

    if duration_seconds > 0:

        orders_per_second = (
            orders_loaded
            / duration_seconds
        )

    else:

        orders_per_second = 0.0

    # =========================================================
    # 14. Report
    # =========================================================

    print()
    print(
        "Transaction ingestion completed."
    )

    print(
        f"  Batch ID: "
        f"{batch_id}"
    )

    print(
        f"  Orders: "
        f"{orders_loaded:,}"
    )

    print(
        f"  Order items: "
        f"{order_items_loaded:,}"
    )

    print(
        f"  Physical batches: "
        f"{transaction_batches_loaded:,}"
    )

    print(
        f"  Duration: "
        f"{duration_seconds:.2f}s"
    )

    print(
        f"  Orders/sec: "
        f"{orders_per_second:,.2f}"
    )

    return {
        "batch_id": str(batch_id),
        "orders": orders_loaded,
        "order_items": order_items_loaded,
        "transaction_batches": (
            transaction_batches_loaded
        ),
        "skipped": 0,
        "duration_seconds": duration_seconds,
        "orders_per_second": orders_per_second,
    }
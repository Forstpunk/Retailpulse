from retailpulse.generators.batch_identity import (
    build_batch_id,
)


def test_same_logical_run_produces_same_batch_id() -> None:
    first = build_batch_id(
        source_system="retailpulse_generator",
        batch_type="ORDER_TRANSACTION",
        logical_run_id="orders-001",
    )

    second = build_batch_id(
        source_system="retailpulse_generator",
        batch_type="ORDER_TRANSACTION",
        logical_run_id="orders-001",
    )

    assert first == second


def test_different_logical_runs_produce_different_batch_ids() -> None:
    first = build_batch_id(
        source_system="retailpulse_generator",
        batch_type="ORDER_TRANSACTION",
        logical_run_id="orders-001",
    )

    second = build_batch_id(
        source_system="retailpulse_generator",
        batch_type="ORDER_TRANSACTION",
        logical_run_id="orders-002",
    )

    assert first != second
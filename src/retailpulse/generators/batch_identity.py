from uuid import UUID, uuid5

RETAILPULSE_NAMESPACE = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def build_batch_id(
    *,
    source_system: str,
    batch_type: str,
    logical_run_id: str,
) -> UUID:
    value = (
        f"{source_system}:"
        f"{batch_type}:"
        f"{logical_run_id}"
    )

    return uuid5(
        RETAILPULSE_NAMESPACE,
        value,
    )
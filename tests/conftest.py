import pytest

from retailpulse.common.database import get_connection
from retailpulse.generators.bootstrap import (
    reference_data_is_ready,
)
from retailpulse.generators.config import (
    GeneratorConfig,
)
from retailpulse.generators.reference_loader import (
    bootstrap_reference_data,
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_reference_data() -> None:
    """
    Most integration tests generate transactions/facts against
    reference data (customers, products, stores, categories,
    suppliers) without bootstrapping it themselves — they were
    written assuming it already exists, which is true for a
    long-lived dev database but not for a fresh one (e.g. CI).

    Bootstrap once per test session, idempotently, sized to the
    largest config any test file uses (GeneratorConfig()
    defaults) so every smaller per-test config's
    reference_data_is_ready() check is satisfied too.
    """

    config = GeneratorConfig()

    with get_connection() as connection:

        if not reference_data_is_ready(
            connection,
            config,
        ):

            bootstrap_reference_data(
                connection,
                config,
            )

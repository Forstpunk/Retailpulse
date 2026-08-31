from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from retailpulse.config.settings import settings
from retailpulse.pipeline.retry import (
    RetryConfig,
    run_with_retry,
)

# A container reporting "started" does not mean PostgreSQL
# is ready to accept connections yet (see the healthcheck in
# docker-compose.yml, which the app itself cannot observe).
# Retrying the initial connect a few times covers the gap
# between "container up" and "accepting connections" without
# a second bespoke retry mechanism — this reuses the same
# RetryConfig/run_with_retry the pipeline stages use.
CONNECT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay_seconds=1.0,
)


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    connection = run_with_retry(
        lambda: psycopg.connect(
            settings.postgres_dsn
        ),
        operation_name="postgres_connect",
        retry_config=CONNECT_RETRY_CONFIG,
    )

    try:
        yield connection

        # Commit anything that was intentionally
        # left open by the caller.
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
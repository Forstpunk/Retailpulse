from contextlib import contextmanager
from collections.abc import Iterator

import psycopg

from retailpulse.config.settings import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(settings.postgres_dsn)

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
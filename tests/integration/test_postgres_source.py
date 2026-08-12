import psycopg

from retailpulse.config.settings import settings


def test_postgres_connection():
    with psycopg.connect(settings.postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            result = cursor.fetchone()

    assert result == ("retailpulse",)
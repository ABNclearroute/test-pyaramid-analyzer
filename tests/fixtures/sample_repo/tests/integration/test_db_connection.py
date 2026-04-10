"""Integration tests for the user repository — requires a real database."""
import pytest
import psycopg2


class UserRepository:
    def __init__(self, conn):
        self._conn = conn

    def find_by_id(self, user_id: int):
        cur = self._conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()

    def create(self, name: str, email: str) -> int:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (name, email),
        )
        self._conn.commit()
        return cur.fetchone()[0]


@pytest.fixture
def db_connection():
    """Provide a real PostgreSQL connection for integration tests."""
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="testdb", user="test", password="test"
    )
    yield conn
    conn.rollback()
    conn.close()


@pytest.mark.integration
class TestUserRepositoryIntegration:
    def test_create_and_find_user(self, db_connection):
        repo = UserRepository(db_connection)
        user_id = repo.create("Alice", "alice@example.com")
        row = repo.find_by_id(user_id)
        assert row is not None
        assert row[1] == "Alice"

    def test_find_nonexistent_user(self, db_connection):
        repo = UserRepository(db_connection)
        row = repo.find_by_id(999_999_999)
        assert row is None

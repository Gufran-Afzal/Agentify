import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.connection import get_db
from backend.app.database.schema import init_db
from backend.app.database.seed import seed_db

TEST_DB_PATH = "test_adaptive_content.db"

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    yield
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture
def test_db():
    conn = sqlite3.connect(TEST_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    seed_db(conn, force_reset=True)
    yield conn
    conn.close()

@pytest.fixture
def client(test_db):
    def override_get_db():
        conn = sqlite3.connect(TEST_DB_PATH, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

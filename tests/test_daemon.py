import sqlite3
import os
import pytest
import sys
import tempfile
from unittest.mock import MagicMock

# Mock requests before importing daemon
mock_requests = MagicMock()
sys.modules["requests"] = mock_requests

import daemon

@pytest.fixture
def temp_db():
    # Use a temporary file for the database
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_init_db(monkeypatch, temp_db):
    # Set the DB_PATH to our temporary file
    monkeypatch.setattr(daemon, "DB_PATH", temp_db)

    # Initialize the database
    conn = daemon.init_db()

    try:
        # Verify the table 'history' exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history';")
        table_exists = cursor.fetchone()
        assert table_exists is not None, "Table 'history' should exist"

        # Verify the columns in 'history'
        cursor.execute("PRAGMA table_info(history);")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'timestamp': 'DATETIME',
            'query': 'TEXT',
            'response': 'TEXT'
        }

        for col, expected_type in expected_columns.items():
            assert col in columns, f"Column '{col}' should exist in 'history' table"
            # SQLite types are not always exact, but should contain the base type
            assert expected_type in columns[col].upper(), f"Column '{col}' should be of type '{expected_type}'"
    finally:
        conn.close()

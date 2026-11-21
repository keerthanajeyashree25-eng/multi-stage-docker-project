"""Database access helpers for the records dashboard."""

import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    """Open a PostgreSQL connection using environment-based settings."""
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "projectdb"),
        user=os.environ.get("DB_USER", "projectuser"),
        password=os.environ.get("DB_PASSWORD", ""),
        connect_timeout=3,
        row_factory=dict_row,
    )


def check_database():
    """Return True when PostgreSQL accepts a simple query."""
    with get_connection() as connection:
        connection.execute("SELECT 1")
    return True


def get_records():
    """Fetch records newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, created_at
            FROM records
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_record(name):
    """Insert a record and return its generated fields."""
    with get_connection() as connection:
        record = connection.execute(
            """
            INSERT INTO records (name)
            VALUES (%s)
            RETURNING id, name, created_at
            """,
            (name,),
        ).fetchone()
    return dict(record)
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_v2.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        self._initialize_db()

    def _get_connection(self):
        """Returns a connection with dictionary-like rows."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        """Initializes the database with schema.sql if it doesn't exist."""
        if not os.path.exists(self.db_path):
            print(f"[Database] Creating new V2 database at {self.db_path}")
            conn = self._get_connection()
            try:
                with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
                conn.commit()
            finally:
                conn.close()

    def execute(self, query, params=()):
        """Executes an INSERT/UPDATE/DELETE query."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def fetchall(self, query, params=()):
        """Executes a SELECT query and returns all results."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def fetchone(self, query, params=()):
        """Executes a SELECT query and returns one result."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

# Singleton instance
db = DatabaseManager()

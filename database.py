import psycopg2
from psycopg2.extras import RealDictCursor
import json
from contextlib import contextmanager
from config import Config

@contextmanager
def get_db():
    """Context manager for PostgreSQL database connections"""
    conn = psycopg2.connect(Config.DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize PostgreSQL database with schema"""
    # Note: Tables are pre-created in PostgreSQL - this function is kept for compatibility
    # but is not called in production (commented out in app.py)
    print("⚠️  Database tables should already exist in PostgreSQL. Skipping init_db().")
    pass

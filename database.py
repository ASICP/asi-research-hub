import sqlite3
import json
from contextlib import contextmanager
from config import Config

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with schema"""
    schema = """
    -- users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        tier TEXT NOT NULL CHECK(tier IN ('student', 'researcher', 'institutional')),
        reason TEXT NOT NULL,
        is_verified BOOLEAN DEFAULT FALSE,
        verification_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );

    -- papers table (your curated content)
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        authors TEXT NOT NULL,
        abstract TEXT,
        year INTEGER,
        source TEXT DEFAULT 'arxiv',
        arxiv_id TEXT,
        doi TEXT,
        pdf_path TEXT,
        pdf_text TEXT,
        asip_funded BOOLEAN DEFAULT FALSE,
        tags TEXT,
        citation_count INTEGER DEFAULT 0,
        added_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (added_by) REFERENCES users(id)
    );

    -- user_bookmarks table
    CREATE TABLE IF NOT EXISTS user_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        paper_id INTEGER NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, paper_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (paper_id) REFERENCES papers(id)
    );

    -- search_logs table (for analytics)
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query TEXT NOT NULL,
        sources TEXT,
        tags_filter TEXT,
        result_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- api_usage table (track Perplexity calls for cost control)
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        month TEXT NOT NULL,
        call_count INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_papers_tags ON papers(tags);
    CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
    CREATE INDEX IF NOT EXISTS idx_papers_asip_funded ON papers(asip_funded);
    CREATE INDEX IF NOT EXISTS idx_search_logs_user ON search_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_search_logs_date ON search_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON user_bookmarks(user_id);
    """
    
    with get_db() as conn:
        conn.executescript(schema)
    
    print("✅ Database initialized successfully")

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

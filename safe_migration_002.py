#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv('DATABASE_URL')
engine = create_engine(database_url)

print("🔧 Running Migration 002...")

with engine.connect() as conn:
    inspector = inspect(engine)

    if 'raw_data' not in [
            col['name'] for col in inspector.get_columns('papers')
    ]:
        conn.execute(text("ALTER TABLE papers ADD COLUMN raw_data JSONB;"))
        print("✅ Added raw_data")

    if 'venue' not in [col['name'] for col in inspector.get_columns('papers')]:
        conn.execute(text("ALTER TABLE papers ADD COLUMN venue TEXT;"))
        print("✅ Added venue")

    for col_name, col_type in [('doi', 'VARCHAR(255)'),
                               ('arxiv_id', 'VARCHAR(100)'),
                               ('pdf_path', 'VARCHAR(255)'),
                               ('pdf_text', 'TEXT'),
                               ('citation_count', 'INTEGER DEFAULT 0'),
                               ('asip_funded', 'BOOLEAN DEFAULT FALSE'),
                               ('added_by', 'VARCHAR(255)'), ('tags', 'TEXT')]:
        if col_name not in [
                col['name'] for col in inspector.get_columns('papers')
        ]:
            conn.execute(
                text(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type};"))
            print(f"✅ Added {col_name}")

    if 'tags' in inspector.get_table_names():
        for col_name, col_type in [('paper_count', 'INTEGER DEFAULT 0'),
                                   ('last_used', 'TIMESTAMP'),
                                   ('slug', 'VARCHAR(100)'),
                                   ('category', 'VARCHAR(50)'),
                                   ('description', 'TEXT')]:
            if col_name not in [
                    col['name'] for col in inspector.get_columns('tags')
            ]:
                conn.execute(
                    text(
                        f"ALTER TABLE tags ADD COLUMN {col_name} {col_type};"))
                print(f"✅ Added tags.{col_name}")

    if 'paper_tags' in inspector.get_table_names():
        if 'confidence' not in [
                col['name'] for col in inspector.get_columns('paper_tags')
        ]:
            conn.execute(
                text(
                    "ALTER TABLE paper_tags ADD COLUMN confidence DECIMAL(3, 2);"
                ))
            print("✅ Added confidence")

    try:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_papers_raw_data ON papers USING gin (raw_data);"
            ))
        print("✅ Created index")
    except:
        pass

    conn.commit()
    print("\n✅ Migration complete!")
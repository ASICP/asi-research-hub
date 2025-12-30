import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ara_v2.app import create_app
from ara_v2.utils.database import db
from sqlalchemy import text, inspect

def check_column_exists():
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('papers')]
    return 'url' in columns

def run_migration():
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("DATABASE MIGRATION: Add URL Column to Papers")
        print("=" * 60)
        if check_column_exists():
            print("✅ Column 'url' already exists. No migration needed!\n")
            return
        print("🔄 Adding 'url' column to papers table...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE papers ADD COLUMN url VARCHAR(500)"))
                conn.commit()
                print("✅ Added 'url' column")
                try:
                    conn.execute(text("CREATE INDEX idx_papers_url ON papers(url)"))
                    conn.commit()
                    print("✅ Created index on url column")
                except Exception as e:
                    print(f"⚠️  Index creation skipped: {e}")
            print("\n✨ Migration completed successfully!\n")
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise

if __name__ == '__main__':
    run_migration()
    
"""
Check database type and run migration to add url column to papers table.
Works in both local and Replit environments.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (works in both local and Replit)
load_dotenv()

def check_database_type():
    """Check what database type is being used."""
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/ara_v2')

    print("=" * 60)
    print("DATABASE CONFIGURATION")
    print("=" * 60)
    print(f"Database URL: {database_url}")

    # Parse database type from URL
    if database_url.startswith('postgresql'):
        db_type = 'PostgreSQL'
    elif database_url.startswith('sqlite'):
        db_type = 'SQLite'
    elif database_url.startswith('mysql'):
        db_type = 'MySQL'
    else:
        db_type = 'Unknown'

    print(f"Database Type: {db_type}")
    print("=" * 60)

    return database_url, db_type

def check_column_exists(engine):
    """Check if url column already exists in papers table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('papers')]
    return 'url' in columns

def run_migration(database_url, db_type):
    """Run the migration to add url column."""
    try:
        engine = create_engine(database_url)

        # Check if column already exists
        if check_column_exists(engine):
            print("\n✅ Column 'url' already exists in papers table. No migration needed.")
            return

        print(f"\nRunning migration for {db_type}...")

        with engine.connect() as conn:
            # PostgreSQL and SQLite both support this syntax
            conn.execute(text("ALTER TABLE papers ADD COLUMN url VARCHAR(500)"))

            # Create index (optional)
            try:
                conn.execute(text("CREATE INDEX idx_papers_url ON papers(url)"))
                print("✅ Created index on url column")
            except Exception as e:
                print(f"⚠️  Index creation failed (may already exist): {e}")

            conn.commit()

        print("✅ Migration completed successfully!")
        print("   - Added 'url' column to papers table")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your database is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Verify database permissions")
        raise

if __name__ == '__main__':
    print("\n🔍 Checking database configuration...\n")
    database_url, db_type = check_database_type()

    print("\n🚀 Running migration...\n")
    run_migration(database_url, db_type)

    print("\n✨ All done! You can now upload papers via URL.")

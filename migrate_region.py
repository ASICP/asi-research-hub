"""
Migration script to add region field to users table
"""
import sqlite3
from config import Config

def migrate():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Add region column
        cursor.execute("""
            ALTER TABLE users ADD COLUMN region TEXT
        """)
        print("✅ Added region column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  region column already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    migrate()

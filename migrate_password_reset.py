"""
Migration script to add password reset fields to users table
"""
import sqlite3
from config import Config

def migrate():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Add password_reset_token column
        cursor.execute("""
            ALTER TABLE users ADD COLUMN password_reset_token TEXT
        """)
        print("✅ Added password_reset_token column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  password_reset_token column already exists")
        else:
            raise
    
    try:
        # Add password_reset_expires column
        cursor.execute("""
            ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP
        """)
        print("✅ Added password_reset_expires column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⏭️  password_reset_expires column already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    migrate()

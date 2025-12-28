
import os
from sqlalchemy import text
from ara_v2.app import create_app
from ara_v2.utils.database import db

def run_migration():
    """
    Safely adds the 'source_id' column to the 'papers' table.
    Works for both SQLite and PostgreSQL.
    """
    print("Initializing application context...")
    app = create_app()
    
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
        print(f"Target Database: {db_uri.split('://')[0]}://***")
        
        try:
            # We use the underlying engine to execute raw SQL for DDL
            with db.engine.connect() as conn:
                print("Attempting to add 'source_id' column...")
                
                # Check if column exists first (naive check by selecting from it)
                try:
                    conn.execute(text("SELECT source_id FROM papers LIMIT 1"))
                    print("✓ Column 'source_id' already exists. No action needed.")
                    return
                except Exception:
                    # Column likely missing, proceed to add it
                    conn.rollback()
                    pass
                
                # Add the column
                try:
                    conn.execute(text("ALTER TABLE papers ADD COLUMN source_id VARCHAR(255)"))
                    conn.commit()
                    print("✅ SUCCESS: Added 'source_id' column to 'papers' table.")
                    
                except Exception as e:
                    if "duplicate" in str(e).lower() or "exists" in str(e).lower():
                        print("✓ Column 'source_id' already exists (caught exception).")
                    else:
                        print(f"❌ ERROR adding source_id: {str(e)}")

                # --- MIGRATION 2: Add 'confidence' to 'paper_tags' ---
                print("\nChecking 'paper_tags' table for 'confidence'...")
                try:
                    conn.execute(text("SELECT confidence FROM paper_tags LIMIT 1"))
                    print("✓ Column 'confidence' already exists.")
                except Exception:
                    conn.rollback()
                    try:
                        print("Adding 'confidence' column...")
                        conn.execute(text("ALTER TABLE paper_tags ADD COLUMN confidence NUMERIC(3, 2) DEFAULT 1.0"))
                        conn.commit()
                        print("✅ SUCCESS: Added 'confidence' to 'paper_tags'.")
                    except Exception as e:
                         print(f"❌ ERROR adding confidence: {str(e)}")
                
                # --- MIGRATION 3: Add 'is_novel_combo' to 'paper_tags' ---
                print("\nChecking 'paper_tags' table for 'is_novel_combo'...")
                try:
                    conn.execute(text("SELECT is_novel_combo FROM paper_tags LIMIT 1"))
                    print("✓ Column 'is_novel_combo' already exists.")
                except Exception:
                    conn.rollback()
                    try:
                        print("Adding 'is_novel_combo' column...")
                        conn.execute(text("ALTER TABLE paper_tags ADD COLUMN is_novel_combo BOOLEAN DEFAULT FALSE"))
                        conn.commit()
                        print("✅ SUCCESS: Added 'is_novel_combo' to 'paper_tags'.")
                    except Exception as e:
                         print(f"❌ ERROR adding is_novel_combo: {str(e)}")
                        
        except Exception as main_e:
            print(f"❌ MIGRATION FAILED: {str(main_e)}")
            print("\nTroubleshooting:")
            print("1. If the database is locked, stop the running application (Step 1).")
            print("2. If using SQLite, ensure you have write permissions to instance/ folder.")

if __name__ == "__main__":
    run_migration()

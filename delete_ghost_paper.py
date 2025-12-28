from ara_v2.app import create_app
from ara_v2.utils.database import db
from ara_v2.models.paper import Paper
from sqlalchemy import text

def clean_database():
    app = create_app()
    with app.app_context():
        # Find paper by simple title match (adjust title as needed)
        # Using a broad delete based on recent creation to be safe
        print("Cleaning up recent ghost papers...")
        
        # 1. Delete papers created in the last hour to be safe
        # Or specifically by title if you know it
        sql = text("DELETE FROM papers WHERE created_at > NOW() - INTERVAL '1 hour'")
        result = db.session.execute(sql)
        db.session.commit()
        
        print(f"Deleted {result.rowcount} recent papers.")
        print("You can now upload freshly.")

if __name__ == "__main__":
    clean_database()

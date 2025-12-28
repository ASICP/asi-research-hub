from ara_v2.app import create_app
from ara_v2.utils.database import db
from ara_v2.models.tag import Tag
from ara_v2.models.paper_tag import PaperTag
from sqlalchemy import func

def fix_counts():
    app = create_app()
    with app.app_context():
        print("Recalculating tag frequencies...")
        
        # Get actual counts from PaperTag table
        # SELECT tag_id, COUNT(*) FROM paper_tags GROUP BY tag_id
        counts = db.session.query(
            PaperTag.tag_id, 
            func.count(PaperTag.paper_id)
        ).group_by(PaperTag.tag_id).all()
        
        updated = 0
        for tag_id, count in counts:
            tag = Tag.query.get(tag_id)
            if tag:
                # Update both frequency and paper_count
                tag.frequency = count
                tag.paper_count = count
                updated += 1
        
        db.session.commit()
        print(f"Updated {updated} tags with correct counts.")

if __name__ == "__main__":
    fix_counts()

import sys
sys.path.insert(0, '.')
from ara_v2.app import create_app
from ara_v2.utils.database import db

app = create_app()
with app.app_context():
      from ara_v2.models.paper import Paper
      from ara_v2.models.tag import Tag
      from ara_v2.models.tag import TagCombo

      paper_count = Paper.query.count()
      tag_count = Tag.query.count()
      combo_count = TagCombo.query.count()

      print(f"Papers in database: {paper_count}")
      print(f"Tags in database: {tag_count}")
      print(f"Tag combinations in database: {combo_count}")

      if paper_count > 0:
          print("\nSample papers with citations:")
          papers = Paper.query.order_by(Paper.citation_count.desc()).limit(3).all()
          for p in papers:
              print(f"  - {p.title[:50]}... (citations: {p.citation_count})")

      if tag_count > 0:
          print("\nSample tags:")
          tags = Tag.query.order_by(Tag.frequency.desc()).limit(5).all()
          for t in tags:
              print(f"  - {t.name} (frequency: {t.frequency})")

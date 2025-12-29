from ara_v2.app import create_app
from ara_v2.models.paper import Paper
from ara_v2.models.tag import Tag
from ara_v2.models.paper_tag import PaperTag
from ara_v2.utils.database import db
import json

app = create_app()
with app.app_context():
    papers = Paper.query.filter(
        Paper.source.in_(['arxiv', 'crossref', 'semantic_scholar']),
        Paper.tags.isnot(None)
    ).all()

    print(f"Found {len(papers)} papers with tags in JSON column")
    migrated = 0

    for paper in papers:
        if paper.tags_relationship.count() > 0:
            continue

        try:
            tag_names = json.loads(paper.tags)
            if not tag_names:
                continue

            print(f"Migrating paper {paper.id}: {len(tag_names)} tags")

            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, frequency=0, paper_count=0)
                    db.session.add(tag)
                    db.session.flush()

                paper_tag = PaperTag(
                    paper_id=paper.id,
                    tag_id=tag.id,
                    confidence=0.8
                )
                db.session.add(paper_tag)

                tag.frequency += 1
                tag.paper_count += 1

            migrated += 1

        except Exception as e:
            print(f"Error migrating paper {paper.id}: {e}")
            continue

    db.session.commit()
    print(f"\nMigrated {migrated} papers from JSON to relationships")
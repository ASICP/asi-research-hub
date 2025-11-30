import sqlite3
import json

conn = sqlite3.connect('asi_research_hub.db')
cursor = conn.cursor()
cursor.execute("SELECT id, tags FROM papers")
rows = cursor.fetchall()

for row in rows:
    id, tags = row
    if tags:
        try:
            json.loads(tags)
        except Exception as e:
            print(f"Error in paper {id}: {e}")
            print(f"Tags: {tags}")

conn.close()

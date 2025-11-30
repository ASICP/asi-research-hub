import sqlite3
from models import Paper

conn = sqlite3.connect('asi_research_hub.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM papers LIMIT 1")
row = cursor.fetchone()
columns = [description[0] for description in cursor.description]
print("DB Columns:", columns)

import inspect
paper_fields = list(Paper.__annotations__.keys())
print("Paper Fields:", paper_fields)

# Check for mismatch
db_set = set(columns)
paper_set = set(paper_fields)

print("In DB but not in Paper:", db_set - paper_set)
print("In Paper but not in DB:", paper_set - db_set)

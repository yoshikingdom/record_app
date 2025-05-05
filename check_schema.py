import sqlite3

DB_NAME = "database.db"  # あなたのDB名に合わせて変更

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("PRAGMA table_info(records)")
columns = c.fetchall()

for col in columns:
    print(col)

conn.close()

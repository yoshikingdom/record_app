# add_notices_table.py
import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        author TEXT NOT NULL
    )
""")

conn.commit()
conn.close()
print("✅ notices テーブルを作成しました。")

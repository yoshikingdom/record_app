# add_column_author.py
import sqlite3

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

try:
    c.execute("ALTER TABLE notifications ADD COLUMN author TEXT")
    print("✅ 'author' カラムを追加しました")
except sqlite3.OperationalError as e:
    print("⚠️ すでに存在しているか、エラー:", e)

conn.commit()
conn.close()

import sqlite3

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

try:
    c.execute("ALTER TABLE notifications ADD COLUMN read INTEGER DEFAULT 0")
    print("✅ 'read' カラムを追加しました")
except sqlite3.OperationalError as e:
    print("⚠️ すでにカラムが存在しているか、別のエラー:", e)

conn.commit()
conn.close()

# add_notifications_table.py
import sqlite3

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# 通知テーブルの作成
c.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    record_id INTEGER,
    comment_id INTEGER,
    is_read INTEGER DEFAULT 0,
    created_at TEXT
)
""")

conn.commit()
conn.close()
print("✅ notifications テーブルを作成しました")

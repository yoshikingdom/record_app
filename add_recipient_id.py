import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE notifications ADD COLUMN recipient_id INTEGER")
    print("✅ recipient_id カラムを追加しました。")
except sqlite3.OperationalError as e:
    print("⚠️ すでに追加済みかエラー:", e)

conn.commit()
conn.close()

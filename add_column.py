import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE records ADD COLUMN created_at TEXT")
    print("✅ 'created_at' カラムを追加しました")
except sqlite3.OperationalError as e:
    print("⚠️ エラー:", e)

conn.commit()
conn.close()

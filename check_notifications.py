import sqlite3

DB_NAME = "database.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
SELECT notifications.id, users.username, notifications.record_id, notifications.comment_id, notifications.is_read, notifications.created_at
FROM notifications
LEFT JOIN users ON notifications.user_id = users.id
ORDER BY notifications.created_at DESC
""")

rows = c.fetchall()
conn.close()

print("🔔 通知一覧:")
for row in rows:
    print(f"ID: {row[0]}, 宛先: {row[1]}, 記録ID: {row[2]}, コメントID: {row[3]}, 既読: {row[4]}, 時間: {row[5]}")

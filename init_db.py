import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# 授業記録テーブルを削除して作成
c.execute("DROP TABLE IF EXISTS records")
c.execute("""
    CREATE TABLE records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        content TEXT,
        homework TEXT,
        next_plan TEXT
    )
""")

# コメントテーブル（parent_idを含むスレッド対応構造）
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""
    CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER,
        author TEXT,
        comment TEXT,
        created_at TEXT,
        parent_id INTEGER DEFAULT NULL
    )
""")

conn.commit()
conn.close()

print("✅ データベースを初期化しました！")

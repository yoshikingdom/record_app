import sqlite3
from werkzeug.security import generate_password_hash  # ← 追加

conn = sqlite3.connect("database.db")
c = conn.cursor()

# ユーザーテーブル
c.execute("DROP TABLE IF EXISTS users")
c.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
""")

# ✅ ハッシュ化したパスワードで登録
users = [
    ("teacher1", generate_password_hash("pass123"), "teacher"),
    ("student1", generate_password_hash("pass456"), "student"),
    ("student2", generate_password_hash("pass789"), "student")
]
c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users)

# records テーブル
c.execute("DROP TABLE IF EXISTS records")
c.execute("""
    CREATE TABLE records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        content TEXT,
        homework TEXT,
        next_plan TEXT,
        student_id INTEGER
    )
""")

# コメントテーブル
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""
    CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER,
        author TEXT,
        comment TEXT,
        created_at TEXT,
        parent_id INTEGER
    )
""")

conn.commit()
conn.close()

print("✅ データベース初期化完了（ハッシュ化対応済み）")

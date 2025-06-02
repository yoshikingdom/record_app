import sqlite3
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "database.db"

conn = sqlite3.connect(DB_NAME)
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
    ("teacher1", generate_password_hash(os.getenv("TEACHER_PASS")), "teacher"),
    ("student1", generate_password_hash(os.getenv("STUDENT1_PASS")), "student"),
    ("student2", generate_password_hash(os.getenv("STUDENT2_PASS")), "student")
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
        student_id INTEGER,
        created_at TEXT
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

# 通知テーブル
c.execute("DROP TABLE IF EXISTS notifications")
c.execute("""
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER,
        record_id INTEGER,
        comment_id INTEGER,
        read INTEGER,
        created_at TEXT,
        author TEXT
    )
""")

# お知らせテーブル
c.execute("DROP TABLE IF EXISTS notices")
c.execute("""
    CREATE TABLE notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        created_at TEXT,
        author TEXT
    )
""")

# 通知テーブル
c.execute("DROP TABLE IF EXISTS notifications")
c.execute("""
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER,   -- 通知を受け取るユーザーID
        record_id INTEGER,      -- 対象の授業記録
        comment_id INTEGER,     -- 対象のコメント
        read INTEGER DEFAULT 0, -- 既読フラグ（0:未読, 1:既読）
        created_at TEXT,
        author TEXT             -- 通知を発したユーザー
    )
""")


conn.commit()
conn.close()

print("✅ データベース初期化完了（ハッシュ化対応済み）")

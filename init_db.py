import sqlite3

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

# サンプルユーザー登録（講師＋生徒2名）
c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", [
    ("teacher1", "pass123", "teacher"),
    ("student1", "pass456", "student"),
    ("student2", "pass789", "student")
])

# ✅ records テーブル（title と student_id を含む）
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

print("✅ データベース初期化完了（title対応済み）")

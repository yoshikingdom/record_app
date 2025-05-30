import sqlite3

DB_NAME = "database.db"  # あなたのDB名に合わせて変更

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("📋 notices テーブルのカラム構造:\n")

c.execute("PRAGMA table_info(notices)")
columns = c.fetchall()

if not columns:
    print("⚠️ notices テーブルが見つかりませんでした。")
else:
    print(f"{'カラム名':<15} {'型':<10} {'NOT NULL':<10} {'主キー':<10}")
    print("-" * 50)
    for col in columns:
        name = col[1]
        col_type = col[2]
        not_null = "✅" if col[3] == 1 else ""
        primary_key = "✅" if col[5] == 1 else ""
        print(f"{name:<15} {col_type:<10} {not_null:<10} {primary_key:<10}")

conn.close()

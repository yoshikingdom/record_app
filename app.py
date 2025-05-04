from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3

app = Flask(__name__)

DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            content TEXT,
            homework TEXT,
            next_plan TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            author TEXT,
            comment TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM records ORDER BY date DESC")
    records = c.fetchall()
    conn.close()
    return render_template("index.html", records=records)

@app.route("/add", methods=["GET", "POST"])
def add_record():
    if request.method == "POST":
        date = request.form["date"]
        content = request.form["content"]
        homework = request.form["homework"]
        next_plan = request.form["next_plan"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO records (date, content, homework, next_plan) VALUES (?, ?, ?, ?)",
                  (date, content, homework, next_plan))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/record/<int:record_id>", methods=["GET", "POST"])
def record_detail(record_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if request.method == "POST":
        author = request.form["author"]
        comment = request.form["comment"]
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("INSERT INTO comments (record_id, author, comment, created_at) VALUES (?, ?, ?, ?)",
                  (record_id, author, comment, created_at))
        conn.commit()

    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    record = c.fetchone()
    c.execute("SELECT * FROM comments WHERE record_id = ? ORDER BY created_at ASC", (record_id,))
    comments = c.fetchall()
    conn.close()
    return render_template("record_detail.html", record=record, comments=comments)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

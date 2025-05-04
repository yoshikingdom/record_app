from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "database.db"

def get_comments_tree(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM comments WHERE record_id = ? ORDER BY created_at ASC", (record_id,))
    comments = c.fetchall()
    conn.close()

    # ツリー構造にする
    comment_dict = {c[0]: {'id': c[0], 'record_id': c[1], 'author': c[2], 'comment': c[3], 'created_at': c[4], 'parent_id': c[5], 'children': []} for c in comments}
    root_comments = []

    for comment in comment_dict.values():
        if comment['parent_id']:
            parent = comment_dict.get(comment['parent_id'])
            if parent:
                parent['children'].append(comment)
        else:
            root_comments.append(comment)

    return root_comments

@app.route("/")
def index():
    conn = sqlite3.connect(DB_NAME)
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

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO records (date, content, homework, next_plan) VALUES (?, ?, ?, ?)",
                  (date, content, homework, next_plan))
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add.html")

@app.route("/record/<int:record_id>", methods=["GET", "POST"])
def record_detail(record_id):
    if request.method == "POST":
        author = request.form["author"]
        comment = request.form["comment"]
        parent_id = request.form.get("parent_id") or None

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO comments (record_id, author, comment, created_at, parent_id) VALUES (?, ?, ?, ?, ?)",
                  (record_id, author, comment, datetime.now().isoformat(), parent_id))
        conn.commit()
        conn.close()

        return redirect(url_for("record_detail", record_id=record_id))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    record = c.fetchone()
    conn.close()

    comments = get_comments_tree(record_id)

    return render_template("record_detail.html", record=record, comments=comments)

if __name__ == "__main__":
    app.run(debug=True)

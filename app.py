from flask import flash
from flask import make_response
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DB_NAME = "database.db"

# ユーザー初期化

def init_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", [
            ("teacher1", "pass123", "teacher"),
            ("student1", "pass456", "student")
        ])
        print("⭐ ユーザー初期登録完了")
    conn.commit()
    conn.close()

init_users()

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

from datetime import datetime

def get_comments_tree(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM comments WHERE record_id = ? ORDER BY created_at ASC", (record_id,))
    comments = c.fetchall()
    conn.close()

    # ID → コメント辞書
    comment_dict = {}
    for cmt in comments:
        try:
            formatted_time = datetime.fromisoformat(cmt[4]).strftime('%Y/%m/%d %H:%M')
        except Exception:
            formatted_time = cmt[4]  # 念のため fallback

        comment_dict[cmt[0]] = {
            'id': cmt[0],
            'record_id': cmt[1],
            'author': cmt[2],
            'comment': cmt[3],
            'created_at': formatted_time,  # ← 加工済み！
            'parent_id': cmt[5],
            'children': []
        }

    root_comments = []
    for comment in comment_dict.values():
        if comment['parent_id']:
            parent = comment_dict.get(comment['parent_id'])
            if parent:
                parent['children'].append(comment)
        else:
            root_comments.append(comment)

    return root_comments


from flask import flash

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        user_data = c.fetchone()
        conn.close()

        if user_data and password == user_data[2]:
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user)
            flash("✅ ログインに成功しました！")
            return redirect(url_for("index"))
        else:
            flash("❌ ログインに失敗しました。ユーザー名またはパスワードが間違っています。")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if current_user.role == "teacher":
        # 講師はすべての記録を見られる
        c.execute("""
            SELECT records.*, users.username 
            FROM records 
            LEFT JOIN users ON records.student_id = users.id 
            ORDER BY date DESC
        """)
    else:
        # 生徒は自分の記録だけ
        c.execute("""
            SELECT records.*, users.username 
            FROM records 
            LEFT JOIN users ON records.student_id = users.id 
            WHERE student_id = ? 
            ORDER BY date DESC
        """, (current_user.id,))

    records = c.fetchall()
    conn.close()
    return render_template("index.html", records=records)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_record():
    if current_user.role != "teacher":
        return "このページは講師専用です", 403

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        title = request.form["title"]
        content = request.form["content"]
        homework = request.form["homework"]
        next_plan = request.form["next_plan"]
        student_id = request.form["student_id"]

        c.execute("INSERT INTO records (date, title, content, homework, next_plan, student_id) VALUES (?, ?, ?, ?, ?, ?)",
          (date, title, content, homework, next_plan, student_id))

        flash("✅ 授業記録を追加しました！", "success")

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    # ✅ 生徒一覧を取得してフォームに渡す
    c.execute("SELECT id, username FROM users WHERE role = 'student'")
    students = c.fetchall()
    conn.close()
    return render_template("add.html", students=students)

@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT author, record_id FROM comments WHERE id = ?", (comment_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return "コメントが見つかりません", 404

    author, record_id = result

    # 講師 or 投稿者本人のみ削除可
    if current_user.role != "teacher" and current_user.username != author:
        conn.close()
        return "削除権限がありません", 403

    # 論理削除（内容だけ変更）
    c.execute("UPDATE comments SET comment = '[削除済み]' WHERE id = ?", (comment_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("record_detail", record_id=record_id))


@app.route("/record/<int:record_id>", methods=["GET", "POST"])
@login_required
def record_detail(record_id):
    if request.method == "POST":
        author = current_user.username
        comment = request.form["comment"]
        parent_id = request.form.get("parent_id") or None
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO comments (record_id, author, comment, created_at, parent_id) VALUES (?, ?, ?, ?, ?)",
                  (record_id, author, comment, datetime.now().isoformat(), parent_id))
        conn.commit()
        conn.close()
        flash("💬 コメントを投稿しました！", "success")  # ← ✅ 追加
        return redirect(url_for("record_detail", record_id=record_id))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    record = c.fetchone()
    conn.close()
    comments = get_comments_tree(record_id)
    return render_template("record_detail.html", record=record, comments=comments, user=current_user)

from flask import flash

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, current_user.id))
        if c.fetchone():
            flash("❗そのユーザー名は既に使われています", "danger")
        else:
            c.execute("UPDATE users SET username = ?, password = ? WHERE id = ?",
                      (new_username, new_password, current_user.id))
            conn.commit()
            conn.close()
            flash("✅ 情報を更新しました。再ログインしてください。", "success")
            logout_user()
            return redirect(url_for("login"))
        conn.close()
    
    return render_template("settings.html", user=current_user)

@app.route("/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
def edit_record(record_id):
    if current_user.role != "teacher":
        return "このページは講師専用です", 403

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        title = request.form["title"]
        content = request.form["content"]
        homework = request.form["homework"]
        next_plan = request.form["next_plan"]

        c.execute("""
            UPDATE records
            SET date = ?, title = ?, content = ?, homework = ?, next_plan = ?
            WHERE id = ?
        """, (date, title, content, homework, next_plan, record_id))
        flash("✅ 編集が完了しました！")
        conn.commit()
        conn.close()
        return redirect(url_for("record_detail", record_id=record_id))

    # GET: 記録を取得
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    record = c.fetchone()

    # 🔒 記録が見つからない場合
    if record is None:
        conn.close()
        return "記録が見つかりませんでした", 404

    # 生徒の名前を取得
    student_id = record[6]
    c.execute("SELECT username FROM users WHERE id = ?", (student_id,))
    student = c.fetchone()
    student_name = student[0] if student else "不明"

    conn.close()
    return render_template("edit.html", record=record, student_name=student_name)




@app.route("/set_theme", methods=["POST"])
def set_theme():
    theme = request.form["theme"]
    resp = make_response(redirect(request.referrer or url_for("index")))
    resp.set_cookie("theme", theme, max_age=60*60*24*30)  # 30日間有効
    return resp


if __name__ == "__main__":
    app.run(debug=True)

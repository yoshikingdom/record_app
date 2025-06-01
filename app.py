from dotenv import load_dotenv
import os
load_dotenv()  # .envファイルの読み込み
from flask import flash
from flask import make_response
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = None  # ✅ 自動メッセージを無効化


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
        teacher_pass = os.getenv("TEACHER1_PASSWORD")
        student_pass = os.getenv("STUDENT1_PASSWORD")

        c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", [
            ("teacher1", generate_password_hash(teacher_pass), "teacher"),
            ("student1", generate_password_hash(student_pass), "student")
        ])
        print("⭐ ユーザー初期登録完了")
    conn.commit()
    conn.close()

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

        if user_data and check_password_hash(user_data[2], password):  # ← ここを修正
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
    query = request.args.get("q", "").strip()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if current_user.role == "teacher":
        if query:
            c.execute("""
                SELECT records.*, users.username 
                FROM records 
                LEFT JOIN users ON records.student_id = users.id 
                WHERE records.title LIKE ? 
                    OR records.content LIKE ? 
                    OR records.date LIKE ? 
                    OR users.username LIKE ?
                ORDER BY date DESC
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        else:
            c.execute("""
                SELECT records.*, users.username 
                FROM records 
                LEFT JOIN users ON records.student_id = users.id 
                ORDER BY date DESC
            """)
    else:
        if query:
            c.execute("""
                SELECT records.*, users.username 
                FROM records 
                LEFT JOIN users ON records.student_id = users.id 
                WHERE student_id = ? AND (records.title LIKE ? OR records.content LIKE ? OR records.date LIKE ?)
                ORDER BY date DESC
            """, (current_user.id, f"%{query}%", f"%{query}%", f"%{query}%"))
        else:
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
        created_at = datetime.now().isoformat()

        c.execute("""INSERT INTO records 
            (date, title, content, homework, next_plan, student_id, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, title, content, homework, next_plan, student_id, created_at))

        conn.commit()
        conn.close()
        flash("✅ 授業記録を追加しました！")
        return redirect(url_for("index"))

    c.execute("SELECT id, username FROM users WHERE role = 'student'")
    students = c.fetchall()
    conn.close()
    return render_template("add.html", students=students)

@app.route("/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_record(record_id):
    if current_user.role != "teacher":
        return "このページは講師専用です", 403

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    flash("🗑️ 記録を削除しました")
    return redirect(url_for("index"))



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
        created_at = datetime.now().isoformat()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # コメントを追加
        c.execute("""
            INSERT INTO comments (record_id, author, comment, created_at, parent_id)
            VALUES (?, ?, ?, ?, ?)
        """, (record_id, author, comment, created_at, parent_id))
        comment_id = c.lastrowid

        # 通知の宛先を決める
        notification_targets = set()

        # ▼ 対象の生徒に通知（ただし自分自身以外）
        c.execute("SELECT student_id FROM records WHERE id = ?", (record_id,))
        student = c.fetchone()
        if student and student[0] != current_user.id:
            notification_targets.add(student[0])

        # ▼ 親コメントの投稿者にも通知（ただし自分自身以外）
        if parent_id:
            c.execute("SELECT author FROM comments WHERE id = ?", (parent_id,))
            parent_author = c.fetchone()
            if parent_author:
                c.execute("SELECT id FROM users WHERE username = ?", (parent_author[0],))
                parent_user = c.fetchone()
                if parent_user and parent_user[0] != current_user.id:
                    notification_targets.add(parent_user[0])

        # ▼ 生徒からの投稿 → 先生にも通知（仮に「全講師」に通知）
        if current_user.role == "student":
            c.execute("SELECT id FROM users WHERE role = 'teacher'")
            teachers = c.fetchall()
            for teacher in teachers:
                if teacher[0] != current_user.id:
                    notification_targets.add(teacher[0])

        # 通知登録（author列を追加）
        for target_id in notification_targets:
            c.execute("""
                INSERT INTO notifications (recipient_id, record_id, comment_id, read, created_at, author)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (target_id, record_id, comment_id, created_at, current_user.username))



        conn.commit()
        conn.close()
        flash("💬 コメントを投稿しました！")
        return redirect(url_for("record_detail", record_id=record_id))

    # GETの場合
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    record = c.fetchone()
    conn.close()
    comments = get_comments_tree(record_id)
    return render_template("record_detail.html", record=record, comments=comments, user=current_user)



@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]

        # パスワードをハッシュ化
        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # ユーザー名が他の人と被っていないか確認
        c.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, current_user.id))
        if c.fetchone():
            flash("❗そのユーザー名は既に使われています", "danger")
        else:
            c.execute("UPDATE users SET username = ?, password = ? WHERE id = ?",
                      (new_username, hashed_password, current_user.id))
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

@app.route("/notifications")
@login_required
def notifications():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 通知を取得（共通）
    c.execute("""
        SELECT n.id, r.title, n.record_id, n.created_at, u.username AS author, n.read
        FROM notifications n
        JOIN records r ON n.record_id = r.id
        JOIN comments cmt ON n.comment_id = cmt.id
        JOIN users u ON cmt.author = u.username
        WHERE n.recipient_id = ?
        ORDER BY n.created_at DESC
    """, (current_user.id,))
    notifications = c.fetchall()

    # 既読に更新
    c.execute("UPDATE notifications SET read = 1 WHERE recipient_id = ?", (current_user.id,))
    conn.commit()
    conn.close()

    return render_template("notifications.html", notifications=notifications)


@app.route("/notifications/mark_read/<int:notif_id>")
@login_required
def mark_notification_read(notif_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ✅ 自分宛ての通知のみ既読にする
    c.execute("""
        UPDATE notifications 
        SET read = 1 
        WHERE id = ? AND recipient_id = ?
    """, (notif_id, current_user.id))

    # 通知の記録IDを取得してリダイレクト
    c.execute("SELECT record_id FROM notifications WHERE id = ?", (notif_id,))
    result = c.fetchone()
    record_id = result[0] if result else None

    conn.commit()
    conn.close()

    if record_id:
        return redirect(url_for("record_detail", record_id=record_id))
    else:
        return redirect(url_for("notifications"))

@app.context_processor
def inject_unread_notifications():
    if current_user.is_authenticated:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND read = 0", (current_user.id,))
        count = c.fetchone()[0]
        conn.close()
        return dict(unread_count=count)
    return dict(unread_count=0)

#  お知らせ一覧のルート
@app.route("/notices")
@login_required
def notices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM notices ORDER BY created_at DESC")
    notices = c.fetchall()
    conn.close()
    return render_template("notices.html", notices=notices)

@app.route("/notices/new", methods=["GET", "POST"])
@login_required
def new_notice():
    if current_user.role != "teacher":
        return "このページは講師専用です", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        created_at = datetime.now().isoformat()
        author = current_user.username

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO notices (title, content, created_at, author)
            VALUES (?, ?, ?, ?)
        """, (title, content, created_at, author))
        conn.commit()
        conn.close()

        flash("✅ お知らせを投稿しました！", "success")
        return redirect(url_for("notices"))

    return render_template("new_notice.html")

@app.route("/notices/<int:notice_id>")
@login_required
def notice_detail(notice_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM notices WHERE id = ?", (notice_id,))
    notice = c.fetchone()
    conn.close()

    if not notice:
        return "お知らせが見つかりません", 404

    return render_template("notice_detail.html", notice=notice)


if __name__ == "__main__":
    app.run(debug=True)

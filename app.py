import math
from flask import Flask, redirect, render_template, request, session, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

from scripts.utils import login_required, calculate_level, apology
from scripts.utils import format_date, currently_logged_in, validate_input
from scripts.utils import assign_activity, is_user_admin, CARD_LIMIT_PER_PAGE
from scripts.utils import calculate_pages, LOG_LIMIT_PER_PAGE, INBOX_LIMIT_PER_PAGE
from scripts.database import db, DBTool

from blueprints.users import users
from blueprints.admin import admin

app = Flask(__name__)
app.register_blueprint(users, url_prefix="/users")
app.register_blueprint(admin, url_prefix="/admin")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.context_processor
def global_variables() -> dict:
    user_text = "Not logged in"
    notifications = 0
    if session.get("user_id"):
        notifications = db.execute("""SELECT COUNT(*) AS count
                                      FROM inbox
                                      WHERE user_id = ? AND has_read = 0
                                      """, session.get("user_id"))[0]["count"]
        level = calculate_level(session.get('experience'))
        user_text = f"{session.get('username')} | Level {level}"
    return {"user": user_text, "notifications": notifications}


@app.template_global()
def logged_in() -> bool:
    return currently_logged_in()


@app.template_global()
def is_admin() -> bool:
    return is_user_admin()


@app.errorhandler(404)
def page_not_found(error):
    return apology("404 Page Not Found"), 404


@app.errorhandler(403)
def forbidden(error):
    return apology("403 Forbidden"), 403


@app.errorhandler(401)
def unauthorized(error):
    return apology("401 Unauthorized"), 401


@app.errorhandler(500)
def internal_server_error(error):
    return apology("500 Internal Server Error"), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    post_count = db.execute("SELECT COUNT(*) AS count FROM posts")[0]["count"]
    pages = calculate_pages(request.args.get("page"),
                            CARD_LIMIT_PER_PAGE, post_count)
    posts = db.execute("""SELECT users.username AS author,
                                 posts.id, posts.content, posts.title
                          FROM posts
                          JOIN users ON users.id = posts.user_id
                          ORDER BY posts.id DESC
                          LIMIT ?
                          OFFSET ?
                          """, CARD_LIMIT_PER_PAGE, pages["offset"])
    return render_template("home.html", posts=posts, current_page=pages["current_page"],
                           page_count=pages["page_count"])


@app.route("/leaderboard")
def leaderboard():
    users = db.execute("""SELECT username, experience
                          FROM users
                          ORDER BY experience DESC
                          LIMIT 100""")
    length = len(users)
    for i in range(length):
        users[i]["level"] = calculate_level(users[i]["experience"])
    return render_template("leaderboard.html", users=users, length=length)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        username = request.form.get("username")
        if not validate_input(password, username):
            return apology("Missing fields!")
        if session.get("username") == username:
            return apology("You're already logged in as this user!")

        profile = db.execute("""SELECT id, username, password, experience
                                FROM users WHERE username = ?""", username)
        if not profile:
            return apology("Username is not recognized!")

        if not check_password_hash(profile[0]["password"], password):
            return apology("Password is incorrect!")

        session["user_id"] = profile[0]["id"]
        session["username"] = profile[0]["username"]
        session["experience"] = profile[0]["experience"]

        DBTool.insert_history("login", "#")

        return redirect("/home")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        username = request.form.get("username")
        if not validate_input(email, password, confirm_password, username):
            return apology("Missing fields!")

        username_taken = db.execute("SELECT username FROM users WHERE username = ?",
                                    username)
        if username_taken:
            return render_template("register.html", validation=True,
                                   form_data={"username": username, "password": password,
                                              "confirm_password": confirm_password, "email": email})

        PASSWORD_LIMIT = 50
        if len(password) > PASSWORD_LIMIT:
            return apology(f"Password must not be greater than {PASSWORD_LIMIT} characters!")
        USERNAME_LIMIT = 30
        if len(username) > USERNAME_LIMIT:
            return apology(f"Username must not be greater than {USERNAME_LIMIT} characters!")

        hashed_password = generate_password_hash(password)
        db.execute("""INSERT INTO users (email, username, password, experience, date_registered)
                      VALUES (?, ?, ?, ?, ?)
                      """, email, username, hashed_password, 0, date.today())

        user_id = db.execute("""SELECT id FROM users WHERE username = ?""",
                             username)[0]["id"]
        db.execute("""INSERT INTO history (user_id, activity_type, link, date_occured)
                      VALUES (?, ?, ?, ?)""", user_id, "register",
                   f"/users/{username}", date.today())

        return redirect("/login")

    return render_template("register.html", validation=False)


@app.route("/logout")
@login_required
def logout():
    DBTool.insert_history("logout", "/")
    session.clear()
    return redirect("/")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if not validate_input(title, content):
            return apology("Missing fields!")

        TITLE_LIMIT = 50
        if len(title) > TITLE_LIMIT:
            return apology(f"Title must be not be greater than {TITLE_LIMIT} characters!")
        CONTENT_LIMIT = 2000
        if len(content) > CONTENT_LIMIT:
            return apology(f"Content must be not be greater than {CONTENT_LIMIT} characters!")

        db.execute("INSERT INTO posts (user_id, title, content, date_created) VALUES (?, ?, ?, ?)",
                   session["user_id"], title, content, date.today())
        post_id = db.execute("SELECT id FROM posts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                             session["user_id"])[0]["id"]

        post_link = f"/users/{session['username']}/posts/{post_id}"
        DBTool.insert_history("create", post_link)
        DBTool.update_exp(100)

        return redirect(post_link)

    return render_template("create.html")


@app.route("/history")
@login_required
def history():
    if not request.args.get("page"):
        return redirect("/history?page=1")

    log_count = db.execute("SELECT COUNT(*) AS count FROM history WHERE user_id = ?",
                           session.get("user_id"))[0]["count"]
    pages = calculate_pages(request.args.get("page"),
                            LOG_LIMIT_PER_PAGE, log_count)
    data = db.execute("""SELECT *
                         FROM history
                         WHERE user_id = ?
                         ORDER BY id DESC
                         LIMIT ?
                         OFFSET ?
                         """, session["user_id"], LOG_LIMIT_PER_PAGE, pages["offset"])

    length = len(data)
    for i in range(length):
        data[i]["count"] = i + 1 + pages["offset"]
        data[i]["date"] = format_date(data[i]["date_occured"])
        data[i]["activity"] = assign_activity(data[i]["activity_type"])

    return render_template("history.html", data=data, length=length,
                           current_page=pages["current_page"],
                           page_count=pages["page_count"])


@app.route("/inbox")
@login_required
def inbox():
    inbox_count = db.execute("SELECT COUNT(*) AS count FROM inbox WHERE user_id = ?",
                             session.get("user_id"))[0]["count"]
    pages = calculate_pages(request.args.get("page"), INBOX_LIMIT_PER_PAGE,
                            inbox_count)
    data = db.execute("""SELECT *
                         FROM inbox
                         WHERE user_id = ?
                         ORDER BY id DESC
                         LIMIT ?
                         OFFSET ?
                         """, session.get("user_id"), INBOX_LIMIT_PER_PAGE, pages["offset"])
    db.execute("UPDATE inbox SET has_read = 1 WHERE user_id = ?",
               session.get("user_id"))
    return render_template("inbox.html", data=data, current_page=pages["current_page"],
                           page_count=pages["page_count"])


if __name__ == "__main__":
    app.run(debug=True)

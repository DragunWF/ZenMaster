from functools import wraps
from flask import Blueprint, render_template, session, request, abort, redirect

from scripts.utils import apology, validate_input, login_required
from scripts.utils import format_date, is_user_admin, sort_data_by_id
from scripts.database import db

admin = Blueprint("admin", __name__, static_folder="static",
                  template_folder="templates")


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") and not is_user_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_function


def query_reports(content: str) -> list:
    report_table = f"{content}_reports"
    reports = db.execute(f"""
    SELECT {report_table}.id, {report_table}.reason,
           {report_table}.date_created, users.username AS reporter,
           {report_table}.{content}_id
    FROM {report_table}
    JOIN users ON users.id = {report_table}.reporter_id
    """)

    authors = {}
    reported_content = db.execute(f"""
    SELECT {content}s.id AS {content}_id, users.id AS user_id, users.username
    FROM {report_table}
    JOIN {content}s ON {content}s.id = {report_table}.{content}_id
    JOIN users ON users.id = {content}s.user_id
    """)

    # Map content authors to reports to determine the reported user
    for data in reported_content:
        authors[data[f"{content}_id"]] = data["username"]
    for i in range(len(reports)):
        reports[i]["reported_user"] = authors[reports[i][f"{content}_id"]]
        reports[i]["date"] = format_date(reports[i]["date_created"])

    return reports


@admin.route("/dashboard", methods=["GET", "POST"])
@login_required
@admin_required
def index():
    if request.method == "POST":
        return redirect("/admin")

    reports = sort_data_by_id([*query_reports("comment"),
                               *query_reports("post")])
    for i in range(len(reports)):
        is_post = "post_id" in reports[i].keys()
        reports[i]["content"] = "Post" if is_post else "Comment"

    return render_template("admin.html", reports=reports)


@admin.route("/delete/post/<int:post_id>", methods=["POST"])
@login_required
@admin_required
def delete_post(post_id: int):
    db.execute("DELETE FROM posts WHERE id = ?", post_id)
    return redirect("/admin")


@admin.route("/delete/comment/<int:comment_id>", methods=["POST"])
@login_required
@admin_required
def delete_comment(comment_id: int):
    db.execute("DELETE FROM comments WHERE id = ?", comment_id)
    return redirect("/admin")


@admin.route("/ban/user/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id: int):
    db.execute("INSERT INTO banned_users (user_id) VALUES (?)", user_id)
    db.execute("DELETE FROM posts WHERE user_id = ?", user_id)
    db.execute("DELETE FROM comments WHERE user_id = ?", user_id)
    return redirect("/admin/dashboard")


@admin.route("/delete/reports/<int:report_id>", methods=["POST"])
@login_required
@admin_required
def delete_report(report_id: int):
    content_type = request.form.get("content_type")
    db.execute(f"DELETE FROM {content_type}_reports WHERE id = ?",
               report_id)
    return redirect("/admin/dashboard")

from flask import Blueprint, render_template, session, request, abort, redirect
from datetime import date

from scripts.utils import login_required, calculate_level, apology
from scripts.utils import format_date, currently_logged_in, validate_input
from scripts.utils import assign_activity, calculate_pages, CARD_LIMIT_PER_PAGE
from scripts.utils import COMMENT_LIMIT_PER_PAGE
from scripts.database import db, DBTool

users = Blueprint("users", __name__, static_folder="static",
                  template_folder="templates")


def report_content(reported_user: str, reason: str, content_id: int, content: str):
    if reported_user == session.get("username"):
        return apology("You cannot report yourself!")
    if not reason:
        return apology("You must input a reason to report content!")
    if len(reason) > 500:
        return apology("Your reason must not be greater than 500 characters!")

    db.execute(f"""INSERT INTO {content}_reports ({content}_id, reporter_id, reason, date_created)
                   VALUES (?, ?, ?, ?)""",
               content_id, session.get("user_id"), reason, date.today())
    DBTool.insert_history("report", "#")

    profile_link = f"/users/{reported_user}"
    if content == "post":
        return redirect(f"{profile_link}/{content}s/{content_id}")

    post_id = db.execute("""
              SELECT posts.id AS post_id
              FROM comments
              JOIN posts ON posts.id = comments.post_id
              WHERE comments.id = ?
              """, content_id)[0]["post_id"]

    return redirect(f"{profile_link}/posts/{post_id}")


@users.route("/<string:username>")
def user_profile(username):
    user_data = db.execute("SELECT id, description, experience FROM users WHERE username = ?",
                           username)
    if not user_data:
        return abort(404)

    profile = user_data[0]
    post_count = db.execute("""SELECT COUNT(*) AS count
                               FROM posts
                               JOIN users ON posts.user_id = users.id
                               WHERE username = ?""",
                            username)[0]["count"]
    pages = calculate_pages(request.args.get("page"), CARD_LIMIT_PER_PAGE,
                            post_count)
    posts = db.execute("""SELECT id, title, content
                          FROM posts
                          WHERE user_id = ?
                          LIMIT ?
                          OFFSET ?
                          """, profile["id"], CARD_LIMIT_PER_PAGE, pages["offset"])
    level = calculate_level(profile["experience"])
    if profile["description"] is None:
        profile["description"] = "Default description..."

    return render_template("profile.html", visited_username=username,
                           description=profile["description"], level=level,
                           posts=posts, current_page=pages["current_page"],
                           page_count=pages["page_count"])


@users.route("/<string:username>/posts/<int:post_id>", methods=["GET", "POST"])
def user_post(username: str, post_id: int):
    if request.method == "POST":
        if not session.get("user_id"):
            return redirect("/login")

        comment = request.form.get("content")
        if not comment:
            return apology("Your comment is empty!")
        if len(comment) > 2000:
            return apology("Your comment must not be greater than 2000 characters!")

        author_id = db.execute("""SELECT users.id
                                  FROM posts
                                  JOIN users ON posts.user_id = users.id
                                  WHERE users.username = ?""", username)

        db.execute("""INSERT INTO comments (user_id, post_id, content, date_created)
                      VALUES (?, ?, ?, ?)""",
                   session["user_id"], post_id, comment, date.today())
        # db.execute("""INSERT INTO inbox (user_id, content, has_read)
        #               VALUES (?, 'A user has commented on your post', 1)""", author_id)

        DBTool.insert_history("comment", request.url)
        DBTool.update_exp(25)

        return redirect(request.path)

    # Post Content
    data = db.execute("""
           SELECT posts.title, posts.content, posts.date_created
           FROM posts
           JOIN users ON users.id = posts.user_id
           WHERE posts.id = ? AND users.username = ?
           """, post_id, username)
    if not data:
        return abort(404)
    post = data[0]

    comment_count = db.execute("""SELECT COUNT(*) AS count
                                  FROM comments
                                  WHERE post_id = ?""", post_id)[0]["count"]
    pages = calculate_pages(request.args.get("page"), COMMENT_LIMIT_PER_PAGE,
                            comment_count)
    comments = db.execute("""
           SELECT comments.id, users.username,
                  comments.content, comments.date_created
           FROM comments
           JOIN users ON users.id = comments.user_id
           WHERE comments.post_id = ?
           ORDER BY comments.id DESC
           LIMIT ?
           OFFSET ?
           """, post_id, COMMENT_LIMIT_PER_PAGE, pages["offset"])

    # Get information on likes
    likes = db.execute("SELECT * FROM likes WHERE post_id = ?", post_id)
    likes_count = len(likes)
    liked_post = False
    for data in likes:
        if data["user_id"] == session.get("user_id"):
            liked_post = True
            break
    is_user_author = session.get("username") == username

    # Like state is capitalized for typography purposes
    # but lowercased when read in code
    like_state = "Like" if not liked_post else "Unlike"

    return render_template("post.html", author=username, comments=comments,
                           title=post["title"], content=post["content"],
                           date_created=format_date(post["date_created"]),
                           is_user_author=is_user_author, post_id=post_id,
                           likes=len(likes), like_state=like_state,
                           current_page=pages["current_page"],
                           page_count=pages["page_count"])


@users.route("/<string:username>/edit", methods=["GET", "POST"])
@login_required
def user_edit(username):
    user_data = db.execute("SELECT description FROM users WHERE username = ?",
                           username)
    if not username:
        return abort(404)
    if session.get("username") != username:
        return abort(401)

    if request.method == "POST":
        db.execute("UPDATE users SET description = ? WHERE username = ?",
                   request.form.get("description"), username)

        profile_link = f"/users/{username}"
        DBTool.insert_history("edit", profile_link)

        return redirect(profile_link)

    return render_template("edit_user.html", description=user_data[0]["description"],
                           username=username)


@users.route("/<string:username>/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def user_delete_post(username: str, post_id: int):
    if session.get("username") != username:
        return abort(403)
    db.execute("DELETE FROM comments WHERE post_id = ?", post_id)
    db.execute("DELETE FROM posts WHERE id = ?", post_id)
    DBTool.insert_history("delete", "#")
    return redirect(f"/users/{username}")


@users.route("/<string:username>/posts/<int:post_id>/like", methods=["POST"])
@login_required
def user_like_post(username: str, post_id: int):
    link = f"/users/{username}/posts/{post_id}"
    author_id = db.execute("""SELECT users.id AS author_id
                              FROM posts
                              JOIN users ON posts.user_id = users.id
                              WHERE users.username = ?
                              """, username)[0]["author_id"]

    if request.form.get("action").lower() == "unlike":
        db.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?",
                   session.get("user_id"), post_id)
        # db.execute("""INSERT INTO inbox (user_id, content, has_read)
        #               VALUES (?, 'Someone liked your post!', 0)""", author_id)
        DBTool.insert_history("unlike", link)
    else:
        db.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
                   session.get("user_id"), post_id)
        # db.execute("""INSERT INTO inbox (user_id, content, has_read)
        #               VALUES (?, 'Someone unliked your post!', 0)""", author_id)
        DBTool.insert_history("like", link)

    return redirect(link)


@users.route("/<string:username>/posts/<int:post_id>/report", methods=["POST"])
@login_required
def user_report_post(username: str, post_id: int):
    return report_content(username, request.form.get("reason"),
                          post_id, "post")


@users.route("/<string:username>/comments/<int:comment_id>/report", methods=["POST"])
@login_required
def user_report_comment(username: str, comment_id: int):
    return report_content(username, request.form.get("reason"),
                          comment_id, "comment")

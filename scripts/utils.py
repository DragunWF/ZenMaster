import math
from functools import wraps
from flask import g, request, redirect, url_for, session, render_template
from scripts.database import db

HISTORY_ACTIVITIES = {
    "like": "You liked a post.",
    "unlike": "You unliked a post",
    "comment": "You commented on a post.",
    "create": "You created a post.",
    "edit": "You edited your profile description.",
    "register": "You registered your account.",
    "login": "You logged in",
    "logout": "You logged out manually",
    "report": "You reported a post!",
}
CARD_LIMIT_PER_PAGE = 12
LOG_LIMIT_PER_PAGE = 30
INBOX_LIMIT_PER_PAGE = 30
COMMENT_LIMIT_PER_PAGE = 20
MONTHS = ("January", "February", "March", "April", "May",
          "June", "July", "August", "September", "October",
          "November", "December")


def currently_logged_in() -> bool:
    return bool(session.get("user_id"))


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not currently_logged_in():
            return redirect("/login")
        return func(*args, **kwargs)
    return decorated_function


def is_user_admin() -> bool:
    admins = [i["user_id"]
              for i in db.execute("SELECT user_id FROM admins")]
    return session.get("user_id") in admins


def apology(message: str):
    return render_template("apology.html", message=message)


def calculate_level(experience: int) -> int:
    points_required = 100
    level = 0
    while experience // points_required != 0:
        level += 1
        points_required += 100
    return level


def format_date(date: str) -> str:
    date_attributes = [int(x) for x in date.split("-")]
    formatted_month = MONTHS[int(date_attributes[1]) - 1]
    return f"{formatted_month} {date_attributes[2]}, {date_attributes[0]}"


def validate_input(*args) -> bool:
    return all(args)


def assign_activity(activity_type: str) -> str:
    if not activity_type in HISTORY_ACTIVITIES:
        return "Unknown"
    return HISTORY_ACTIVITIES[activity_type]


def sort_data_by_id(data: list) -> list:
    for i in range(len(data)):
        for j in range(len(data) - 1):
            if data[j]["id"] < data[j + 1]["id"]:
                temp = data[j]
                data[j] = data[j + 1]
                data[j + 1] = temp
    return data


def calculate_pages(page_arg: str, limit: int, item_count: int) -> dict:
    # Page arg indicates the nth page of a certain data, "?page=1"
    page = int(page_arg) if page_arg else 1
    return {
        "current_page": page,
        "offset": limit * (page - 1),
        "page_count": math.ceil(item_count / limit) if item_count > limit else 1
    }

from cs50 import SQL
from flask import session
from datetime import date

db = SQL("sqlite:///data.db")


class DBTool:
    @staticmethod
    def insert_history(activity_type: str, link: str):
        if session.get("user_id"):
            db.execute("""INSERT INTO history (user_id, activity_type, link, date_occured)
                          VALUES (?, ?, ?, ?)""",
                       session.get("user_id"), activity_type, link, date.today())

    @staticmethod
    def update_exp(gain: int):
        db.execute("UPDATE users SET experience = experience + ? WHERE id = ?",
                   gain, session.get("user_id"))
        session["experience"] += gain

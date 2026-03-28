import sqlite3

from flask import Flask, g, current_app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app: Flask) -> None:
    with app.app_context():
        get_db().executescript("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          TEXT PRIMARY KEY,
                event_name  TEXT NOT NULL,
                event_time  TEXT NOT NULL,
                alert_time  TEXT NOT NULL,
                sent        INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            );
        """)

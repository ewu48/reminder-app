from datetime import datetime

from .database import get_db
from .models import Reminder


def _to_reminder(row) -> Reminder:
    return Reminder(
        id=row["id"],
        event_name=row["event_name"],
        event_time=datetime.fromisoformat(row["event_time"]),
        alert_time=datetime.fromisoformat(row["alert_time"]),
        sent=bool(row["sent"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_pending() -> list[Reminder]:
    rows = get_db().execute(
        "SELECT * FROM reminders WHERE sent=0 ORDER BY alert_time"
    ).fetchall()
    return [_to_reminder(r) for r in rows]


def insert(reminder: Reminder) -> None:
    db = get_db()
    db.execute(
        "INSERT INTO reminders (id, event_name, event_time, alert_time, sent, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            reminder.id,
            reminder.event_name,
            reminder.event_time.isoformat(),
            reminder.alert_time.isoformat(),
            int(reminder.sent),
            reminder.created_at.isoformat(),
        ),
    )
    db.commit()


def mark_sent(reminder_id: str) -> None:
    db = get_db()
    db.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
    db.commit()


def delete(reminder_id: str) -> None:
    db = get_db()
    db.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    db.commit()

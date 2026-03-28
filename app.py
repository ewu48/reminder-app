import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "reminders.db")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    topic = "reminders-" + uuid.uuid4().hex[:10]
    config = {"ntfy_topic": topic}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return config


config = load_config()
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", config["ntfy_topic"])

scheduler = BackgroundScheduler(daemon=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          TEXT PRIMARY KEY,
                event_name  TEXT NOT NULL,
                event_time  TEXT NOT NULL,
                alert_time  TEXT NOT NULL,
                sent        INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            )
        """)


def send_notification(reminder_id, event_name, event_time_str):
    event_dt = datetime.fromisoformat(event_time_str)
    formatted = event_dt.strftime("%b %d at %I:%M %p")
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"Reminder: {event_name} is coming up at {formatted}",
            headers={
                "Title": f"\u23f0 {event_name}",
                "Priority": "high",
                "Tags": "bell,calendar",
            },
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[ntfy] Failed to send notification: {e}")
    with get_db() as conn:
        conn.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))


def schedule_job(reminder_id, event_name, event_time_str, alert_time_str):
    alert_dt = datetime.fromisoformat(alert_time_str)
    if alert_dt > datetime.now():
        scheduler.add_job(
            send_notification,
            trigger="date",
            run_date=alert_dt,
            args=[reminder_id, event_name, event_time_str],
            id=reminder_id,
            replace_existing=True,
        )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", ntfy_topic=NTFY_TOPIC)


@app.route("/api/reminders", methods=["GET"])
def list_reminders():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders WHERE sent=0 ORDER BY alert_time"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/reminders", methods=["POST"])
def add_reminder():
    data = request.get_json(force=True)
    event_name = data.get("event_name", "").strip()
    event_time = data.get("event_time", "").strip()
    alert_minutes = data.get("alert_minutes")

    if not event_name or not event_time or alert_minutes is None:
        return jsonify({"error": "event_name, event_time, and alert_minutes are required"}), 400

    try:
        event_dt = datetime.fromisoformat(event_time)
        alert_dt = event_dt - timedelta(minutes=int(alert_minutes))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid event_time or alert_minutes"}), 400

    if alert_dt <= datetime.now():
        return jsonify({"error": "Alert time is already in the past"}), 400

    reminder_id = uuid.uuid4().hex
    with get_db() as conn:
        conn.execute(
            "INSERT INTO reminders (id, event_name, event_time, alert_time, sent, created_at) VALUES (?,?,?,?,0,?)",
            (reminder_id, event_name, event_dt.isoformat(), alert_dt.isoformat(), datetime.now().isoformat()),
        )

    schedule_job(reminder_id, event_name, event_dt.isoformat(), alert_dt.isoformat())
    return jsonify({"id": reminder_id}), 201


@app.route("/api/reminders/<reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    with get_db() as conn:
        conn.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    if scheduler.get_job(reminder_id):
        scheduler.remove_job(reminder_id)
    return "", 204


@app.route("/api/config")
def get_config():
    return jsonify({"ntfy_topic": NTFY_TOPIC})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    with get_db() as conn:
        pending = conn.execute("SELECT * FROM reminders WHERE sent=0").fetchall()
    for r in pending:
        schedule_job(r["id"], r["event_name"], r["event_time"], r["alert_time"])

    scheduler.start()

    print("\n" + "=" * 50)
    print("  Reminder App")
    print("=" * 50)
    print(f"  Web UI  : http://localhost:5000")
    print(f"  ntfy    : https://ntfy.sh/{NTFY_TOPIC}")
    print(f"  Topic   : {NTFY_TOPIC}")
    print("  Subscribe to the topic in the ntfy app")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False)

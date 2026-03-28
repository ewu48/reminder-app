# Reminder App

A lightweight web-based reminder app that sends push notifications to your phone via [ntfy.sh](https://ntfy.sh). Set an event name, event time, and how far in advance you want to be alerted — the app handles the rest in the background.

---

## Features

- Add reminders with a custom event name, date/time, and alert lead time (minutes, hours, or days)
- Receive push notifications on your phone via the free ntfy app
- Reminders persist across restarts (SQLite storage)
- Delete upcoming reminders from the UI
- Clean REST API — ready to extend with voice commands or other interfaces

---

## Screenshots

> Web UI running at `http://localhost:5000`

- Form to add a new reminder with event name, date/time, and alert lead time
- Live list of upcoming reminders with countdown to alert
- ntfy topic displayed in the banner for easy phone setup

---

## Requirements

- Python 3.9+
- A free [ntfy.sh](https://ntfy.sh) account (no sign-up required)
- The **ntfy** app on your phone ([iOS](https://apps.apple.com/us/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy))

---

## Installation

```bash
# Clone the repository
git clone https://github.com/ewu48/reminder-app.git
cd reminder-app

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### 1. Start the server

```bash
python app.py
```

On first run, a unique ntfy topic is generated and saved to `config.json`. The terminal will print something like:

```
==================================================
  Reminder App
==================================================
  Web UI  : http://localhost:5000
  ntfy    : https://ntfy.sh/reminders-8904be9e1c
  Topic   : reminders-8904be9e1c
  Subscribe to the topic in the ntfy app
==================================================
```

### 2. Set up phone notifications

1. Install the **ntfy** app on your phone
2. Tap **+** and subscribe to your unique topic (shown in the terminal and on the web UI)
3. Done — alerts will appear as push notifications at the scheduled time

### 3. Add a reminder

Open `http://localhost:5000` in your browser, fill in:

| Field | Description |
|---|---|
| Event name | What the reminder is for |
| Event date & time | When the event occurs |
| Alert me before | How far in advance to notify (e.g. 15 min, 2 hrs, 1 day) |

Hit **Add Reminder** and you're set.

---

## Running in the Background

To keep the app running after closing the terminal:

```bash
nohup python app.py > app.log 2>&1 &
```

To stop it:

```bash
# Find the process
lsof -i :5000

# Kill it
kill <PID>
```

---

## API Reference

The app exposes a simple REST API, making it easy to integrate voice commands or other frontends.

### `GET /api/reminders`
Returns all pending (unsent) reminders.

```json
[
  {
    "id": "a1b2c3d4",
    "event_name": "Team meeting",
    "event_time": "2026-03-28T14:00:00",
    "alert_time": "2026-03-28T13:45:00",
    "sent": 0,
    "created_at": "2026-03-27T10:00:00"
  }
]
```

### `POST /api/reminders`
Add a new reminder.

**Request body:**
```json
{
  "event_name": "Team meeting",
  "event_time": "2026-03-28T14:00:00",
  "alert_minutes": 15
}
```

**Response:** `201 Created`
```json
{ "id": "a1b2c3d4" }
```

### `DELETE /api/reminders/<id>`
Delete a reminder by ID.

**Response:** `204 No Content`

### `GET /api/config`
Returns the current ntfy topic.

```json
{ "ntfy_topic": "reminders-8904be9e1c" }
```

---

## Project Structure

```
reminder-app/
├── app.py                  # Flask backend, scheduler, ntfy integration
├── requirements.txt        # Python dependencies
├── config.json             # Auto-generated ntfy topic (git-ignored)
├── reminders.db            # SQLite database (git-ignored)
├── app.log                 # Server log when running with nohup (git-ignored)
└── templates/
    └── index.html          # Web UI
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | [Flask](https://flask.palletsprojects.com/) |
| Scheduling | [APScheduler](https://apscheduler.readthedocs.io/) |
| Database | SQLite (via Python `sqlite3`) |
| Notifications | [ntfy.sh](https://ntfy.sh) |
| Frontend | Vanilla HTML/CSS/JS |

---

## Roadmap

- [ ] Voice command interface
- [ ] Recurring reminders (daily, weekly)
- [ ] Multiple notification channels (SMS, email)
- [ ] Mobile-friendly PWA

---

## License

MIT

# Reminder App — Design Document

## Overview

A lightweight, locally-hosted reminder application that accepts an event name, event time, and a configurable lead time, then delivers a push notification to the user's phone at the right moment via [ntfy.sh](https://ntfy.sh).

---

## Goals

- Simple, friction-free reminder creation via a web form
- Reliable delivery of phone push notifications at the scheduled time
- Reminders survive server restarts
- Clean REST API as the contract between UI and backend (enabling future clients, e.g. voice commands)
- Code that is easy to extend without touching existing layers

---

## Non-Goals

- Multi-user support
- Authentication / authorisation
- Cloud hosting or high availability
- Native mobile app

---

## Architecture

The app follows a **layered architecture** with strict one-way dependencies between layers. Each layer only depends on the layer directly below it.

```
┌─────────────────────────────────┐
│           Web UI (Browser)      │  HTML / CSS / Vanilla JS
└────────────────┬────────────────┘
                 │ HTTP (JSON REST)
┌────────────────▼────────────────┐
│         Routes  (routes.py)     │  Request validation, HTTP responses
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│       Service  (services.py)    │  Business logic, scheduling
└──────────┬──────────────┬───────┘
           │              │
┌──────────▼──────┐  ┌────▼──────────────┐
│ Repository      │  │ NtfyClient        │
│ (repository.py) │  │ (notifications.py)│
└──────────┬──────┘  └────────────────────┘
           │
┌──────────▼──────┐
│ SQLite Database │
└─────────────────┘
```

### Layer Responsibilities

| Layer | File | Responsibility |
|---|---|---|
| **Routes** | `app/routes.py` | Parse HTTP requests, validate input, serialize responses. No business logic. |
| **Service** | `app/services.py` | Create/delete reminders, manage the APScheduler jobs, fire notifications. |
| **Repository** | `app/repository.py` | All SQL queries. Returns typed `Reminder` objects, never raw rows. |
| **Notifications** | `app/notifications.py` | Send push notifications via ntfy. Isolated so the backend can be swapped. |
| **Database** | `app/database.py` | Connection lifecycle tied to the Flask application context via `g`. |
| **Models** | `app/models.py` | `Reminder` dataclass — the shared data contract between layers. |
| **Config** | `app/config.py` | Environment-based configuration. Reads from env vars / `.env` file. |

---

## Key Design Decisions

### 1. App Factory Pattern

`create_app(env)` in `app/__init__.py` constructs the Flask application rather than creating a module-level global. This:

- Enables different configs for development vs production
- Makes the app fully testable (create a fresh instance per test)
- Makes dependencies explicit — `NtfyClient`, `BackgroundScheduler`, and `ReminderService` are constructed once and injected

### 2. Service Layer Owns the Scheduler

`ReminderService` holds the `BackgroundScheduler` instance and is the only place that adds or removes jobs. This keeps scheduling logic out of both routes and the repository. The service's `_fire()` method is the single callback for all reminder jobs.

### 3. Scheduler Jobs Push Their Own App Context

APScheduler callbacks run in a background thread outside of any Flask request context. To safely access the database from `_fire()`, the service pushes an explicit application context:

```python
def _fire(self, reminder_id, event_name, event_time):
    self._ntfy.send(...)
    with self._app.app_context():
        repository.mark_sent(reminder_id)
```

This avoids the pitfall of `RuntimeError: Working outside of application context` without requiring a separate DB connection strategy for background jobs.

### 4. Repository Returns Typed Objects

The repository converts SQLite rows into `Reminder` dataclasses before returning them. No layer above the repository ever touches a raw `sqlite3.Row`. This means:

- The rest of the codebase uses `.event_name`, `.alert_time`, etc. (not string keys)
- Changing the DB schema only requires updating `repository.py` and `models.py`

### 5. NtfyClient is Isolated

All ntfy-specific logic lives in `NtfyClient`. The service calls `self._ntfy.send(title, message, ...)` and doesn't know or care about HTTP. To switch to SMS, email, or Pushover, only `NtfyClient` needs to change (or a new client can be injected).

### 6. Configuration Hierarchy

Config is resolved in this order (highest priority first):

```
Environment variable  →  .env file  →  config.json (auto-generated)  →  hardcoded default
```

`NTFY_TOPIC` is persisted to `config.json` on first run so it stays stable across restarts without requiring manual configuration.

---

## Data Model

### `Reminder`

```python
@dataclass
class Reminder:
    id: str            # UUID hex — primary key
    event_name: str    # Human-readable event label
    event_time: datetime  # When the event occurs
    alert_time: datetime  # When the notification fires (event_time - lead)
    sent: bool         # True after the notification has been delivered
    created_at: datetime
```

### SQLite Schema

```sql
CREATE TABLE reminders (
    id          TEXT PRIMARY KEY,
    event_name  TEXT NOT NULL,
    event_time  TEXT NOT NULL,   -- ISO 8601
    alert_time  TEXT NOT NULL,   -- ISO 8601
    sent        INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL    -- ISO 8601
);
```

---

## API

All endpoints accept and return JSON.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `GET` | `/api/reminders` | List all pending (unsent) reminders |
| `POST` | `/api/reminders` | Create a reminder |
| `DELETE` | `/api/reminders/<id>` | Delete a reminder |
| `GET` | `/api/config` | Return current ntfy topic |

### POST `/api/reminders` — Request Body

```json
{
  "event_name": "Team standup",
  "event_time": "2026-04-01T09:00:00",
  "alert_minutes": 15
}
```

`alert_minutes` is always in minutes. The UI converts hours/days to minutes before sending.

---

## Notification Flow

```
User submits form
      │
      ▼
routes.py validates input
      │
      ▼
ReminderService.create()
  ├── Calculates alert_time = event_time - alert_minutes
  ├── Persists Reminder to SQLite
  └── Registers APScheduler job (trigger: date, run_date: alert_time)
                          │
          (at alert_time) │
                          ▼
              ReminderService._fire()
                ├── NtfyClient.send()  ──► ntfy.sh ──► Phone notification
                └── repository.mark_sent()
```

---

## Startup & Restart Recovery

On startup, `ReminderService.reschedule_pending()` queries the DB for all reminders where `sent=0` and re-registers them with the scheduler. This means reminders are not lost if the server is restarted before they fire.

---

## File Structure

```
reminder-app/
├── app/
│   ├── __init__.py       # create_app factory
│   ├── config.py         # Config classes (Dev / Prod)
│   ├── database.py       # DB connection lifecycle
│   ├── models.py         # Reminder dataclass
│   ├── repository.py     # All SQL queries
│   ├── notifications.py  # NtfyClient
│   ├── services.py       # ReminderService (business logic + scheduling)
│   └── routes.py         # Flask Blueprint (HTTP layer)
├── templates/
│   └── index.html        # Single-page web UI
├── run.py                # Entry point — loads .env, calls create_app()
├── requirements.txt
├── .env.example          # Template for environment configuration
├── .gitignore
├── README.md
└── DESIGN.md             # This document
```

---

## Future Extensions

### Voice Commands
The service layer is intentionally decoupled from HTTP. A voice interface would:
1. Parse speech into `event_name`, `event_time`, `alert_minutes`
2. Call `service.create(...)` directly — no HTTP needed

### Recurring Reminders
Add a `recurrence` field to `Reminder` (e.g. `daily`, `weekly`). In `_fire()`, after sending the notification, re-schedule the next occurrence instead of marking as sent.

### Multiple Notification Backends
`NtfyClient` can be replaced or augmented with an `SmtpClient`, `TwilioClient`, etc. The service accepts any object with a `.send(title, message, ...)` interface.

### Testing
The app factory pattern means tests can spin up an isolated instance:
```python
def test_create_reminder():
    app = create_app("testing")
    with app.app_context():
        # test against an in-memory or temp DB
```

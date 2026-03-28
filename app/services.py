import logging
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from . import repository
from .models import Reminder
from .notifications import NtfyClient

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, app: Flask, ntfy: NtfyClient, scheduler: BackgroundScheduler) -> None:
        self._app = app
        self._ntfy = ntfy
        self._scheduler = scheduler

    # ── Public API ────────────────────────────────────────────────────────────

    def list_pending(self) -> list[Reminder]:
        return repository.get_pending()

    def create(self, event_name: str, event_time: datetime, alert_minutes: int) -> Reminder:
        alert_time = event_time - timedelta(minutes=alert_minutes)
        if alert_time <= datetime.now():
            raise ValueError("Alert time is already in the past")

        reminder = Reminder(
            id=uuid.uuid4().hex,
            event_name=event_name,
            event_time=event_time,
            alert_time=alert_time,
            sent=False,
            created_at=datetime.now(),
        )
        repository.insert(reminder)
        self._schedule(reminder)
        logger.info("Created reminder %s: '%s' alerting at %s", reminder.id, event_name, alert_time)
        return reminder

    def delete(self, reminder_id: str) -> None:
        repository.delete(reminder_id)
        if self._scheduler.get_job(reminder_id):
            self._scheduler.remove_job(reminder_id)
        logger.info("Deleted reminder %s", reminder_id)

    def reschedule_pending(self) -> None:
        """Re-enqueue any pending reminders on startup."""
        with self._app.app_context():
            pending = repository.get_pending()
        for reminder in pending:
            self._schedule(reminder)
        if pending:
            logger.info("Rescheduled %d pending reminder(s) from previous session", len(pending))

    # ── Internals ─────────────────────────────────────────────────────────────

    def _schedule(self, reminder: Reminder) -> None:
        if reminder.alert_time <= datetime.now():
            return
        self._scheduler.add_job(
            self._fire,
            trigger="date",
            run_date=reminder.alert_time,
            args=[reminder.id, reminder.event_name, reminder.event_time],
            id=reminder.id,
            replace_existing=True,
        )

    def _fire(self, reminder_id: str, event_name: str, event_time: datetime) -> None:
        formatted = event_time.strftime("%b %d at %I:%M %p")
        self._ntfy.send(
            title=f"\u23f0 {event_name}",
            message=f"Reminder: {event_name} is coming up at {formatted}",
            tags=["bell", "calendar"],
        )
        with self._app.app_context():
            repository.mark_sent(reminder_id)
        logger.info("Fired reminder %s for '%s'", reminder_id, event_name)

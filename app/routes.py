import logging
from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

from .services import ReminderService

logger = logging.getLogger(__name__)


def create_blueprint(service: ReminderService) -> Blueprint:
    bp = Blueprint("main", __name__)

    @bp.get("/")
    def index():
        return render_template("index.html", ntfy_topic=current_app.config["NTFY_TOPIC"])

    @bp.get("/api/reminders")
    def list_reminders():
        return jsonify([r.to_dict() for r in service.list_pending()])

    @bp.post("/api/reminders")
    def add_reminder():
        data = request.get_json(force=True, silent=True) or {}
        event_name = (data.get("event_name") or "").strip()
        event_time_str = (data.get("event_time") or "").strip()
        alert_minutes_raw = data.get("alert_minutes")

        if not event_name:
            return jsonify({"error": "event_name is required"}), 400
        if not event_time_str:
            return jsonify({"error": "event_time is required"}), 400
        if alert_minutes_raw is None:
            return jsonify({"error": "alert_minutes is required"}), 400

        try:
            event_time = datetime.fromisoformat(event_time_str)
            alert_minutes = int(alert_minutes_raw)
            if alert_minutes < 1:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid event_time or alert_minutes"}), 400

        try:
            reminder = service.create(event_name, event_time, alert_minutes)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"id": reminder.id}), 201

    @bp.delete("/api/reminders/<reminder_id>")
    def delete_reminder(reminder_id: str):
        service.delete(reminder_id)
        return "", 204

    @bp.get("/api/config")
    def get_config():
        return jsonify({"ntfy_topic": current_app.config["NTFY_TOPIC"]})

    @bp.app_errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found"}), 404

    @bp.app_errorhandler(500)
    def internal_error(_e):
        logger.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    return bp

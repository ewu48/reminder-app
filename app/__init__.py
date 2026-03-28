import logging
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from .config import config as app_config
from .database import close_db, init_db
from .notifications import NtfyClient
from .routes import create_blueprint
from .services import ReminderService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_BASE_DIR = Path(__file__).parent.parent


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__, template_folder=str(_BASE_DIR / "templates"))
    app.config.from_object(app_config[env])

    init_db(app)
    app.teardown_appcontext(close_db)

    ntfy = NtfyClient(app.config["NTFY_BASE_URL"], app.config["NTFY_TOPIC"])
    scheduler = BackgroundScheduler(daemon=True)
    service = ReminderService(app, ntfy, scheduler)

    service.reschedule_pending()
    scheduler.start()

    app.register_blueprint(create_blueprint(service))

    return app

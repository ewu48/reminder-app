import json
import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def _load_or_create_topic() -> str:
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())["ntfy_topic"]
    topic = f"reminders-{uuid.uuid4().hex[:10]}"
    config_path.write_text(json.dumps({"ntfy_topic": topic}, indent=2))
    return topic


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key")
    DATABASE_PATH: str = str(BASE_DIR / "reminders.db")
    NTFY_BASE_URL: str = os.environ.get("NTFY_BASE_URL", "https://ntfy.sh")
    NTFY_TOPIC: str = os.environ.get("NTFY_TOPIC") or _load_or_create_topic()


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

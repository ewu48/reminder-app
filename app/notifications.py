import logging

import requests

logger = logging.getLogger(__name__)


class NtfyClient:
    def __init__(self, base_url: str, topic: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.topic = topic

    def send(
        self,
        title: str,
        message: str,
        priority: str = "high",
        tags: list[str] | None = None,
    ) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/{self.topic}",
                data=message.encode("utf-8"),
                headers={
                    "Title": title,
                    "Priority": priority,
                    "Tags": ",".join(tags or ["bell"]),
                },
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Notification sent: %s", title)
            return True
        except requests.RequestException:
            logger.exception("Failed to send ntfy notification")
            return False

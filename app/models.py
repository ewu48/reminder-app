from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reminder:
    id: str
    event_name: str
    event_time: datetime
    alert_time: datetime
    sent: bool
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_name": self.event_name,
            "event_time": self.event_time.isoformat(),
            "alert_time": self.alert_time.isoformat(),
            "sent": self.sent,
            "created_at": self.created_at.isoformat(),
        }

from datetime import datetime, timezone

from common.db import db

alerts_coll = db["alerts"]


def send_alert(message):
    alert = {
        "message": message,
        "created_at": datetime.now(timezone.utc)
    }

    alerts_coll.insert_one(alert)

    print(f"ALERT: {message}")
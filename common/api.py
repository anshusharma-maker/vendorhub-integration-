import requests


def get_token(url, client_id, client_secret):
    response = requests.post(
        url,
        json={
            "client_id": client_id,
            "client_secret": client_secret
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


import time


def call_api(method, url, token, body=None, retry=True):
    max_attempts = 3 if retry else 1

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_attempts):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=30
            )

            if 400 <= response.status_code < 500:
                return response

            if response.status_code >= 500:
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue

                return response

            return response

        except requests.RequestException:
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue

            raise



from datetime import datetime, timezone
from common.db import db

api_logs_coll = db["api_logs"]


def log_api_call(url, headers, body, status, reply):
    log_headers = headers.copy() if headers else {}
    log_body = body.copy() if isinstance(body, dict) else body

    if "Authorization" in log_headers:
        log_headers["Authorization"] = "***"

    if isinstance(log_body, dict):
        if "token" in log_body:
            log_body["token"] = "***"

        if "client_secret" in log_body:
            log_body["client_secret"] = "***"

        if "secret" in log_body:
            log_body["secret"] = "***"

    api_logs_coll.insert_one({
        "url": url,
        "headers": log_headers,
        "body": log_body,
        "status": status,
        "reply": reply,
        "created_at": datetime.now(timezone.utc)
    })


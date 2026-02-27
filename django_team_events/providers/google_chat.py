import logging

import requests

from django_team_events.config import get_gchat_webhook

logger = logging.getLogger(__name__)


def send(message: str) -> None:
    webhook = get_gchat_webhook()
    if not webhook:
        return

    try:
        response = requests.post(webhook, json={"text": message}, timeout=5)
        response.raise_for_status()
    except Exception:
        logger.exception("django-team-events: failed to send Google Chat notification")

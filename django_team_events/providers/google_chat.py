import logging

import requests

from django_team_events.config import GCHAT_WEBHOOK

logger = logging.getLogger(__name__)


def send(message: str) -> None:
    if not GCHAT_WEBHOOK:
        return

    try:
        response = requests.post(GCHAT_WEBHOOK, json={"text": message}, timeout=5)
        response.raise_for_status()
    except Exception:
        logger.exception("django-team-events: failed to send Google Chat notification")

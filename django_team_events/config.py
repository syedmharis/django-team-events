import logging
import os

logger = logging.getLogger(__name__)

GCHAT_WEBHOOK = os.environ.get("DJANGO_TEAM_EVENTS_GCHAT_WEBHOOK")

if not GCHAT_WEBHOOK:
    logger.warning(
        "DJANGO_TEAM_EVENTS_GCHAT_WEBHOOK is not set. Notifications will not be sent."
    )

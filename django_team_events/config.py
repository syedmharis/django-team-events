from django.conf import settings


def get_gchat_webhook():
    config = getattr(settings, "DJANGO_TEAM_EVENTS", {})
    return config.get("GCHAT_WEBHOOK")

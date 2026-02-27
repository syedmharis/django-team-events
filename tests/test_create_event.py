import itertools
from unittest.mock import MagicMock, patch

import pytest
from django.db import connection, models

from django_team_events import TeamEvents

WEBHOOK_URL = "https://chat.googleapis.com/fake-webhook"

_counter = itertools.count(1)


def make_model(notify_on):
    """Dynamically create a uniquely-named test model with TeamEvents."""
    model_name = f"TestModel{next(_counter)}"

    class Meta:
        app_label = "django_team_events"

    attrs = {
        "__module__": __name__,
        "Meta": Meta,
        "name": models.CharField(max_length=100),
        "team_events": TeamEvents(notify_on=notify_on),
    }
    model = type(model_name, (models.Model,), attrs)

    connection.disable_constraint_checking()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    connection.enable_constraint_checking()

    return model


@pytest.mark.django_db(transaction=True)
def test_create_event_triggers_webhook():
    model = make_model(notify_on=["create"])

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="test")

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == WEBHOOK_URL
    assert "text" in call_args[1]["json"]


@pytest.mark.django_db(transaction=True)
def test_no_webhook_when_env_missing():
    model = make_model(notify_on=["create"])

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=None):
        with patch("django_team_events.providers.google_chat.requests.post") as mock_post:
            model.objects.create(name="test")

    mock_post.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_notify_on_respected():
    model = make_model(notify_on=["update"])

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post") as mock_post:
            model.objects.create(name="test")

    mock_post.assert_not_called()

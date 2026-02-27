import itertools
from unittest.mock import MagicMock, patch

import pytest
from django.db import connection, models

from django_team_events import TeamEvents

WEBHOOK_URL = "https://chat.googleapis.com/fake-webhook"

_counter = itertools.count(300)


def make_model(notify_on, **team_events_kwargs):
    model_name = f"DeleteTestModel{next(_counter)}"

    class Meta:
        app_label = "django_team_events"

    attrs = {
        "__module__": __name__,
        "Meta": Meta,
        "name": models.CharField(max_length=100),
        "team_events": TeamEvents(notify_on=notify_on, **team_events_kwargs),
        "__str__": lambda self: self.name,
    }
    model = type(model_name, (models.Model,), attrs)

    connection.disable_constraint_checking()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    connection.enable_constraint_checking()

    return model


@pytest.mark.django_db(transaction=True)
def test_delete_event_triggers_webhook():
    model = make_model(notify_on=["delete"])
    instance = model.objects.create(name="Alice")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.delete()

    mock_post.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_delete_message_format():
    model = make_model(notify_on=["delete"])
    instance = model.objects.create(name="Alice")
    pk = instance.pk

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.delete()

    text = mock_post.call_args[1]["json"]["text"]
    assert "Deleted" in text
    assert str(pk) in text
    assert "Alice" in text


@pytest.mark.django_db(transaction=True)
def test_delete_not_triggered_when_not_in_notify_on():
    model = make_model(notify_on=["create", "update"])
    instance = model.objects.create(name="Alice")

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post") as mock_post:
            instance.delete()

    mock_post.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_delete_webhook_failure_does_not_raise():
    model = make_model(notify_on=["delete"])
    instance = model.objects.create(name="Alice")

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", side_effect=Exception("network error")):
            instance.delete()  # must not raise

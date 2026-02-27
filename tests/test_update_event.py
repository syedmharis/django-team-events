import itertools
from unittest.mock import MagicMock, patch

import pytest
from django.db import connection, models

from django_team_events import TeamEvents

WEBHOOK_URL = "https://chat.googleapis.com/fake-webhook"

_counter = itertools.count(100)


def make_model(fields=None):
    model_name = f"UpdateTestModel{next(_counter)}"

    class Meta:
        app_label = "django_team_events"

    base_fields = {
        "__module__": __name__,
        "Meta": Meta,
        "team_events": TeamEvents(notify_on=["update"]),
    }
    if fields:
        base_fields.update(fields)
    else:
        base_fields["name"] = models.CharField(max_length=100)

    model = type(model_name, (models.Model,), base_fields)

    connection.disable_constraint_checking()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    connection.enable_constraint_checking()

    return model


@pytest.mark.django_db(transaction=True)
def test_update_event_triggers_webhook():
    model = make_model()
    instance = model.objects.create(name="original")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "updated"
            instance.save()

    mock_post.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_update_no_meaningful_change_sends_nothing():
    model = make_model()
    instance = model.objects.create(name="same")

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post") as mock_post:
            # Save without changing any field value
            instance.save()

    mock_post.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_update_only_changed_fields_in_message():
    model = make_model(fields={
        "__module__": __name__,
        "Meta": type("Meta", (), {"app_label": "django_team_events"}),
        "team_events": TeamEvents(notify_on=["update"]),
        "name": models.CharField(max_length=100),
        "email": models.CharField(max_length=100),
        "role": models.CharField(max_length=100),
    })
    instance = model.objects.create(name="Alice", email="alice@example.com", role="admin")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.email = "bob@example.com"
            instance.save()

    mock_post.assert_called_once()
    sent_text = mock_post.call_args[1]["json"]["text"]
    assert "name" in sent_text
    assert "email" in sent_text
    assert "role" not in sent_text

import itertools
from unittest.mock import MagicMock, patch

import pytest
from django.db import connection, models

from django_team_events import TeamEvents

WEBHOOK_URL = "https://chat.googleapis.com/fake-webhook"

_counter = itertools.count(400)


def make_model(fields=None, notify_on=("create", "update", "delete"), **team_events_kwargs):
    model_name = f"TemplateTestModel{next(_counter)}"

    class Meta:
        app_label = "django_team_events"

    base = {
        "__module__": __name__,
        "Meta": Meta,
        "name": models.CharField(max_length=100),
        "team_events": TeamEvents(notify_on=list(notify_on), **team_events_kwargs),
        "__str__": lambda self: self.name,
    }
    if fields:
        base.update(fields)

    model = type(model_name, (models.Model,), base)

    connection.disable_constraint_checking()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    connection.enable_constraint_checking()

    return model


def sent_text(mock_post):
    return mock_post.call_args[1]["json"]["text"]


# ---------------------------------------------------------------------------
# Custom create template
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_custom_create_template_applied():
    model = make_model(
        notify_on=["create"],
        template={"create": "New user: {name}"},
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice")

    assert sent_text(mock_post) == "New user: Alice"


@pytest.mark.django_db(transaction=True)
def test_create_falls_back_to_default_when_no_template():
    model = make_model(notify_on=["create"])

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice")

    assert "Created" in sent_text(mock_post)
    assert "🔔" in sent_text(mock_post)


# ---------------------------------------------------------------------------
# Custom update template
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_custom_update_template_applied():
    model = make_model(
        notify_on=["update"],
        template={"update": "Updated user: {name}"},
    )
    instance = model.objects.create(name="Alice")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.save()

    assert sent_text(mock_post) == "Updated user: Bob"


# ---------------------------------------------------------------------------
# Fallback when template key is missing for the action
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_fallback_when_template_key_missing_for_action():
    # template only has "create", not "update"
    model = make_model(
        notify_on=["update"],
        template={"create": "New: {name}"},
    )
    instance = model.objects.create(name="Alice")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.save()

    assert "Updated" in sent_text(mock_post)
    assert "✏️" in sent_text(mock_post)


# ---------------------------------------------------------------------------
# Fallback when template references a missing field
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_fallback_when_template_field_missing():
    model = make_model(
        notify_on=["create"],
        template={"create": "Hello {nonexistent_field}"},
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice")

    # Must not raise, must fall back to default
    mock_post.assert_called_once()
    assert "Created" in sent_text(mock_post)


# ---------------------------------------------------------------------------
# Custom delete template
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_custom_delete_template_applied():
    model = make_model(
        notify_on=["delete"],
        template={"delete": "Goodbye {name}"},
    )
    instance = model.objects.create(name="Alice")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.get_gchat_webhook", return_value=WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.delete()

    assert sent_text(mock_post) == "Goodbye Alice"

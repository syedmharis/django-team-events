import itertools
from unittest.mock import MagicMock, patch

import pytest
from django.db import connection, models

from django_team_events import TeamEvents

WEBHOOK_URL = "https://chat.googleapis.com/fake-webhook"

_counter = itertools.count(200)


def make_model(fields, notify_on=("create", "update"), **team_events_kwargs):
    model_name = f"FilterTestModel{next(_counter)}"

    class Meta:
        app_label = "django_team_events"

    attrs = {
        "__module__": __name__,
        "Meta": Meta,
        "team_events": TeamEvents(notify_on=list(notify_on), **team_events_kwargs),
    }
    attrs.update(fields)
    model = type(model_name, (models.Model,), attrs)

    connection.disable_constraint_checking()
    with connection.schema_editor() as editor:
        editor.create_model(model)
    connection.enable_constraint_checking()

    return model


def get_sent_text(mock_post):
    return mock_post.call_args[1]["json"]["text"]


# ---------------------------------------------------------------------------
# Sensitive field exclusion — create
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_sensitive_fields_excluded_on_create():
    model = make_model({"password": models.CharField(max_length=100)})

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(password="secret123")

    mock_post.assert_called_once()
    assert "password" not in get_sent_text(mock_post)
    assert "secret123" not in get_sent_text(mock_post)


@pytest.mark.django_db(transaction=True)
def test_all_sensitive_field_names_excluded():
    model = make_model({
        "name": models.CharField(max_length=100),
        "password": models.CharField(max_length=100),
        "token": models.CharField(max_length=100),
        "secret": models.CharField(max_length=100),
        "api_key": models.CharField(max_length=100),
        "access_key": models.CharField(max_length=100),
    })

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(
                name="Alice",
                password="p",
                token="t",
                secret="s",
                api_key="a",
                access_key="k",
            )

    mock_post.assert_called_once()
    text = get_sent_text(mock_post)
    for sensitive in ("password", "token", "secret", "api_key", "access_key"):
        assert sensitive not in text


# ---------------------------------------------------------------------------
# Sensitive field exclusion — update
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_sensitive_fields_excluded_on_update():
    model = make_model({
        "name": models.CharField(max_length=100),
        "token": models.CharField(max_length=100),
    }, notify_on=["update"])

    instance = model.objects.create(name="Alice", token="old-token")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.token = "new-token"
            instance.save()

    mock_post.assert_called_once()
    assert "token" not in get_sent_text(mock_post)
    assert "name" in get_sent_text(mock_post)


# ---------------------------------------------------------------------------
# include_fields
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_include_fields_on_create():
    model = make_model(
        {"name": models.CharField(max_length=100), "email": models.CharField(max_length=100)},
        include_fields=["name"],
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice", email="alice@example.com")

    mock_post.assert_called_once()
    text = get_sent_text(mock_post)
    assert "name" in text
    assert "email" not in text


@pytest.mark.django_db(transaction=True)
def test_include_fields_on_update():
    model = make_model(
        {"name": models.CharField(max_length=100), "role": models.CharField(max_length=100)},
        notify_on=["update"],
        include_fields=["name"],
    )
    instance = model.objects.create(name="Alice", role="admin")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.role = "editor"
            instance.save()

    mock_post.assert_called_once()
    text = get_sent_text(mock_post)
    assert "name" in text
    assert "role" not in text


# ---------------------------------------------------------------------------
# exclude_fields
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_exclude_fields_on_create():
    model = make_model(
        {"name": models.CharField(max_length=100), "last_login": models.CharField(max_length=100)},
        exclude_fields=["last_login"],
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice", last_login="2026-01-01")

    mock_post.assert_called_once()
    text = get_sent_text(mock_post)
    assert "name" in text
    assert "last_login" not in text


@pytest.mark.django_db(transaction=True)
def test_exclude_fields_on_update():
    model = make_model(
        {"name": models.CharField(max_length=100), "last_login": models.CharField(max_length=100)},
        notify_on=["update"],
        exclude_fields=["last_login"],
    )
    instance = model.objects.create(name="Alice", last_login="2026-01-01")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            instance.name = "Bob"
            instance.last_login = "2026-02-01"
            instance.save()

    mock_post.assert_called_once()
    text = get_sent_text(mock_post)
    assert "name" in text
    assert "last_login" not in text


# ---------------------------------------------------------------------------
# include_fields overrides sensitive field exclusion
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_include_fields_overrides_sensitive_exclusion():
    model = make_model(
        {"name": models.CharField(max_length=100), "token": models.CharField(max_length=100)},
        include_fields=["name", "token"],
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("django_team_events.providers.google_chat.GCHAT_WEBHOOK", WEBHOOK_URL):
        with patch("django_team_events.providers.google_chat.requests.post", return_value=mock_response) as mock_post:
            model.objects.create(name="Alice", token="abc123")

    mock_post.assert_called_once()
    assert "token" in get_sent_text(mock_post)

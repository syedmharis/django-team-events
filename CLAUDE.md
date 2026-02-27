# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`django-team-events` is a PyPI-distributed Django package that sends team notifications (Google Chat via webhooks) when Django model lifecycle events occur (create, update, delete). It uses Django signals under the hood with per-model configuration via a `TeamEvents` descriptor class.

## Commands

```bash
# Install for development
pip install -e .

# Run tests
pytest

# Run a single test
pytest tests/test_signals.py::test_create_event_sent
```

## Architecture

The signal flow is: **Model Save/Delete → Django Signal → TeamEvents Descriptor → Event Processor → Formatter → Provider → Webhook POST**

### Core Modules

- [django_team_events/__init__.py](django_team_events/__init__.py) — Exports `TeamEvents` as the public API entry point
- [django_team_events/apps.py](django_team_events/apps.py) — `DjangoTeamEventsConfig` AppConfig
- [django_team_events/config.py](django_team_events/config.py) — Reads `DJANGO_TEAM_EVENTS_GCHAT_WEBHOOK` env var; provides defaults
- [django_team_events/signals.py](django_team_events/signals.py) — Listens to `post_save` / `post_delete`; detects action type (create/update/delete); computes field diffs; invokes Event Processor
- [django_team_events/formatter.py](django_team_events/formatter.py) — Pure formatting logic; generates default messages and applies custom templates via `.format()`
- [django_team_events/providers/google_chat.py](django_team_events/providers/google_chat.py) — Isolated HTTP layer; reads webhook from env; catches all exceptions (never raises)

### Dependency Rules (must not be violated)

- `signals` → may import processor
- `processor` → may import `formatter` + `provider`
- `formatter` → pure logic only, no network
- `provider` → isolated HTTP logic only
- `TeamEvents` descriptor → no network logic

No circular dependencies allowed.

### Key Behavioral Constraints

- **Signals must never raise exceptions** — all errors must be caught and logged
- **No transaction side effects** — no DB writes from notification code
- **Update diff detection** — fetch original instance before save, compare fields, skip notification if no meaningful change
- **Sensitive field auto-exclusion** — `password`, `token`, `secret`, `api_key`, `access_key` are stripped unless overridden via `include_fields`
- **Bulk updates not supported** — `QuerySet.update()` and raw SQL are out of scope

### Field Filtering Order (for updates)

1. Start with changed fields
2. Remove sensitive fields
3. Apply `include_fields` (if set)
4. Apply `exclude_fields`

## Testing

- Use `unittest.mock` or `pytest-mock` to mock webhooks — no real HTTP calls allowed in tests
- Target 70% coverage for v0.1.0
- Test categories: model lifecycle, field filtering, template rendering, provider behavior

## Adding a New Provider

Follow the pattern in [django_team_events/providers/google_chat.py](django_team_events/providers/google_chat.py): read config from env, send POST, catch all exceptions, log errors. Providers must be isolated from formatter and signal logic.

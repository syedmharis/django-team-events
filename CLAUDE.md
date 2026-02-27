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
pytest tests/test_create_event.py::test_create_event_triggers_webhook
```

## Architecture

The signal flow is: **Model Save/Delete → Django Signal → TeamEvents Descriptor → Event Processor → Formatter → Provider → Webhook POST**

### Core Modules

- [django_team_events/__init__.py](django_team_events/__init__.py) — Exports `TeamEvents` as the public API entry point
- [django_team_events/apps.py](django_team_events/apps.py) — `DjangoTeamEventsConfig` AppConfig
- [django_team_events/config.py](django_team_events/config.py) — `get_gchat_webhook()` reads `DJANGO_TEAM_EVENTS["GCHAT_WEBHOOK"]` from Django settings
- [django_team_events/team_events.py](django_team_events/team_events.py) — Core logic: `TeamEvents` descriptor wires `pre_save`/`post_save`/`post_delete` signals; handles create/update/delete detection, pre-save snapshot for diff, field filtering, and template application
- [django_team_events/signals.py](django_team_events/signals.py) — Placeholder; signal wiring lives in `team_events.py` via the descriptor
- [django_team_events/formatter.py](django_team_events/formatter.py) — Pure formatting: `format_create()`, `format_update()`, `format_delete()`; no network, no templates
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

### Field Filtering Order (create and update)

1. Start with all fields (create) or changed fields only (update)
2. Remove sensitive fields (`password`, `token`, `secret`, `api_key`, `access_key`) — skipped if `include_fields` is set
3. Apply `include_fields` (if set) — overrides sensitive exclusion
4. Apply `exclude_fields` (if set)

## Testing

- Use `unittest.mock` to mock webhooks — no real HTTP calls in tests
- All test files use dynamic model creation via `type()` with a module-level `itertools.count()` counter for unique model names
- Counter ranges by file: create=1, update=100, field_filtering=200, delete=300, templates=400
- Patch `get_gchat_webhook` at `django_team_events.providers.google_chat.get_gchat_webhook` with `return_value=WEBHOOK_URL` or `return_value=None`
- Always patch both `get_gchat_webhook` and `requests.post` in the same `with` block
- 24 tests, all passing (v0.1.0 complete)

## Adding a New Provider

Follow the pattern in [django_team_events/providers/google_chat.py](django_team_events/providers/google_chat.py): read config from env, send POST, catch all exceptions, log errors. Providers must be isolated from formatter and signal logic.

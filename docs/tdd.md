# TDD Plan — django-team-events

This document defines test-first development plan.

We follow lightweight TDD.

---

## 1. Test Categories

### 1.1 Model Lifecycle Tests

- test_create_event_sent
- test_update_event_sent
- test_delete_event_sent
- test_update_with_no_change_sends_nothing

---

### 1.2 Field Filtering Tests

- test_exclude_fields_removed
- test_include_fields_only_included
- test_sensitive_fields_auto_removed
- test_sensitive_fields_override_allowed

---

### 1.3 Template Tests

- test_custom_create_template_applied
- test_template_missing_field_fallbacks
- test_default_format_when_no_template

---

### 1.4 Provider Tests

- test_google_chat_webhook_called
- test_webhook_failure_does_not_raise
- test_missing_webhook_logs_warning

Webhook must be mocked using unittest.mock or pytest-mock.

No real HTTP calls allowed.

---

## 2. Test Order Strategy

Phase 1:
- Write failing test for create event
- Implement minimal signal + provider

Phase 2:
- Write failing test for update diff
- Implement diff logic

Phase 3:
- Write failing tests for filtering
- Implement filtering logic

Phase 4:
- Write failing tests for template override
- Implement formatting

---

## 3. Testing Principles

- No integration with real Google Chat
- No reliance on external services
- Fast test suite (<2 seconds)
- Isolated tests
- Deterministic behavior

---

## 4. Coverage Goal

Initial target:
70% coverage

After v0.2.0:
85% coverage

Do NOT chase 100% coverage blindly.

---

## 5. Definition of Done

A feature is complete when:

- All related tests pass
- No regression occurs
- No exceptions leak
- README remains accurate
# Architecture — django-team-events

## 1. Overview

django-team-events is a signal-based Django package that listens to model lifecycle events (create, update, delete) and sends formatted notifications to Google Chat via webhook.

The architecture is intentionally simple and layered to avoid overengineering.

---

## 2. High-Level Flow

Model Save/Delete
        ↓
Django Signal (post_save / post_delete)
        ↓
TeamEvents Descriptor (per-model config)
        ↓
Event Processor
        ↓
Formatter
        ↓
Provider (Google Chat)
        ↓
Webhook POST request

---

## 3. Core Components

### 3.1 TeamEvents (Model Descriptor)

Responsible for:
- Storing per-model configuration
- Registering model with signal system
- Providing config access to signal handlers

Must NOT:
- Send messages directly
- Contain provider logic

---

### 3.2 signals.py

Responsible for:
- Listening to post_save and post_delete
- Detecting action type (create / update / delete)
- Computing field diffs
- Invoking Event Processor

Must:
- Be safe
- Never raise exceptions upward
- Be idempotent

---

### 3.3 Event Processor

Responsible for:
- Applying include/exclude logic
- Removing sensitive fields
- Selecting correct template (default or custom)
- Passing final message to provider

---

### 3.4 formatter.py

Responsible for:
- Generating default formatted message
- Applying custom template via `.format()`
- Generating update diff block

No provider logic allowed here.

---

### 3.5 providers/google_chat.py

Responsible for:
- Reading webhook from environment
- Sending POST request
- Catching exceptions
- Logging errors (not raising)

Single provider in v0.1.0.

---

### 3.6 config.py

Responsible for:
- Loading environment variables
- Validating webhook presence
- Providing defaults

---

## 4. Dependency Rules

- signals → may import processor
- processor → may import formatter + provider
- formatter → pure logic
- provider → isolated HTTP logic
- descriptor → no network logic

No circular dependencies allowed.

---

## 5. Design Constraints

- No async in v1
- No database writes
- No background tasks
- No global registry
- Per-model only
- Safe failure guaranteed

---

## 6. Non-Goals (v0.1.0)

- Multiple channels
- Conditional routing
- Rich formatting blocks
- Admin UI
- Event bus architecture
- Audit trail system
<a name="readme-top"></a>

# django-team-events

<div align="center">

  <h3 align="center">Automatic Django Model Activity Notifications</h3>

  <p align="center">
    Lightweight Django package for real-time team notifications on model events.
    <br />
    <br />
    <a href="#installation">Install</a>
    ·
    <a href="#quick-start">Quick Start</a>
    ·
    <a href="#configuration">Configuration</a>
    ·
    <a href="#roadmap">Roadmap</a>
  </p>

</div>

---

## 📌 About The Project

`django-team-events` is a lightweight Django package that automatically sends notifications to your team when important model events occur — such as **create**, **update**, or **delete**.

Built for startup teams and product-driven environments where:

- Important user actions shouldn’t go unnoticed
- Developers don’t want to poll Django admin
- Business logic shouldn’t be cluttered with notification code
- Setup must be simple and predictable

This package uses Django signals under the hood and provides **per-model granular configuration**, giving you clean integration without modifying your core logic.

V1 supports:

- ✅ Google Chat (Incoming Webhooks)
- 🔒 Automatic sensitive field exclusion
- 🎨 Customizable message templates
- 🧠 Smart field diff detection
- 🛡 Safe, non-blocking delivery

Slack support is planned in upcoming releases.

---

## ✨ Features

- Signal-based model tracking
- Per-model configuration via `TeamEvents`
- Automatic detection of created vs updated vs deleted
- Field-level include/exclude controls
- Automatic exclusion of common sensitive fields
- Clean default message formatting
- Customizable message templates
- Webhook-based configuration (via environment variables)
- Never breaks your request cycle

---

## 📦 Installation

```bash
pip install django-team-events
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    ...
    "django_team_events",
]
```

---

## 🔐 Environment Configuration

### Getting Your Google Chat Webhook URL

1. Open **Google Chat** and go to the Space (channel) where you want notifications
2. Click the Space name at the top → **Apps & integrations**
3. Click **Add webhooks**
4. Give it a name (e.g. `django-team-events`) and optionally an avatar URL
5. Click **Save** — copy the generated webhook URL

Add to your `settings.py`:

```python
DJANGO_TEAM_EVENTS = {
    "GCHAT_WEBHOOK": "https://chat.googleapis.com/v1/spaces/XXXXX/messages?key=...",
}
```

Do not hardcode webhooks in your codebase.

---

## ⚡ Quick Start

### 1️⃣ Add `TeamEvents` to Your Model

```python
from django.db import models
from django_team_events import TeamEvents

class User(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=255)

    team_events = TeamEvents(
        notify_on=["create", "update", "delete"],
        exclude_fields=["last_login"],
    )

    def __str__(self):
        return self.email
```

That’s it.

Whenever this model is created, updated, or deleted, your team will receive a notification in Google Chat.

---

## 🔔 Default Message Format

### Create

```
🔔 [User] Created
ID: 12
Object: haris@example.com
Time: 2026-02-27 14:30
```

### Update

```
✏️ [User] Updated
ID: 12
Changes:
- name: Haris → Syed Haris
```

### Delete

```
🗑 [User] Deleted
ID: 12
Object: haris@example.com
```

---

## 🎨 Custom Message Templates

You can override default formatting using templates:

```python
class Agency(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)

    team_events = TeamEvents(
        notify_on=["create", "update"],
        template={
            "create": "🚀 New Agency Registered: {name} by {owner}",
            "update": "✏️ Agency {name} was updated",
        },
        include_fields=["name", "owner"],
    )

    def __str__(self):
        return self.name
```

Templates use Python `.format()` style and can reference model fields.

---

## ⚙️ Configuration Options

| Option | Description |
|--------|------------|
| `notify_on` | List of actions: `"create"`, `"update"`, `"delete"` |
| `include_fields` | Explicit fields to include |
| `exclude_fields` | Fields to ignore |
| `template` | Custom message per action |

---

## 🔒 Sensitive Field Handling

The following field names are automatically excluded:

- password
- token
- secret
- api_key
- access_key

You can override this using `include_fields` or `exclude_fields`.

---

## ⚠️ Limitations (v0.1.0)

- Bulk updates are not tracked
- Async delivery not included
- Single Google Chat channel only
- No conditional routing
- No Slack support (yet)

---

## 🛡 Design Guarantees

- Webhook failures will not crash your application
- No transaction rollbacks
- No recursive signal loops
- Minimal dependencies

---

## 🗺 Roadmap

- Slack webhook provider
- Async support (Celery integration)
- Multiple channel routing
- Conditional rules
- Admin dashboard
- Rich message formatting

---

## 🧪 Development

Clone the repository:

```bash
git clone https://github.com/yourusername/django-team-events.git
cd django-team-events
pip install -e .
```

Run tests:

```bash
pytest
```

---

## 🤝 Contributing

Contributions are welcome.

Before submitting a PR:

- Add tests
- Use type hints
- Keep dependencies minimal
- Maintain backward compatibility

---

## 📄 License

Distributed under the MIT License.

---

<p align="right">(<a href="#readme-top">back to top</a>)</p>

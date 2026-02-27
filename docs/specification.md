# Specification — django-team-events (v0.1.0)

## 1. Scope

This specification defines exact behavior for v0.1.0.

Supported:
- Model create
- Model update
- Model delete
- Google Chat webhook
- Per-model configuration
- Custom templates
- Sensitive field exclusion

---

## 2. Model Integration

A model integrates by adding:

    team_events = TeamEvents(...)

If TeamEvents is not present:
    → Model must not trigger any behavior.

---

## 3. Supported Actions

notify_on accepts:
- "create"
- "update"
- "delete"

If action not included → no notification sent.

---

## 4. Action Detection

### Create
If instance._state.adding is True in post_save → create.

### Update
If post_save and not created → update.

### Delete
Handled via post_delete.

---

## 5. Field Diff Detection (Update Only)

- Fetch original instance before save
- Compare field values
- Include only changed fields
- Exclude auto fields (id, created_at unless explicitly included)

If no meaningful field changed:
    → Do not send notification.

---

## 6. Sensitive Field Exclusion

Automatically excluded field names (case-insensitive):

- password
- token
- secret
- api_key
- access_key

Developer may override via include_fields.

---

## 7. Field Filtering Rules

If include_fields provided:
    → Only those fields are considered.

If exclude_fields provided:
    → Remove those fields.

Filtering order:
1. Start with changed fields (or all fields on create)
2. Remove sensitive fields
3. Apply include_fields (if exists)
4. Apply exclude_fields

---

## 8. Default Message Format

### Create

🔔 [ModelName] Created  
ID: {id}  
Object: {__str__()}  
Time: {timestamp}

### Update

✏️ [ModelName] Updated  
ID: {id}  
Changes:  
- field: old → new

### Delete

🗑 [ModelName] Deleted  
ID: {id}  
Object: {__str__()}

---

## 9. Custom Template Behavior

template must be dict:
{
  "create": "...",
  "update": "...",
  "delete": "..."
}

Uses Python `.format()`.

If field missing:
    → Fail silently and fallback to default format.

---

## 10. Webhook Behavior

- Webhook read from:
  DJANGO_TEAM_EVENTS_GCHAT_WEBHOOK

If not set:
    → Log warning
    → Do not crash

---

## 11. Failure Guarantees

Under no circumstances should:
- Exceptions bubble up to request cycle
- Transactions rollback
- Infinite signal recursion occur

All provider errors must be caught and logged.

---

## 12. Unsupported Behavior

- Bulk updates
- Queryset.update()
- Raw SQL
- Async tasks
- Multiple webhook routing
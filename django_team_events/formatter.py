from datetime import datetime


def format_create(instance, fields: dict) -> str:
    model_name = instance.__class__.__name__
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    field_lines = "\n".join(f"- {k}: {v}" for k, v in fields.items())
    return (
        f"🔔 [{model_name}] Created\n"
        f"ID: {instance.pk}\n"
        f"Object: {instance}\n"
        f"Time: {timestamp}\n"
        f"{field_lines}"
    )


def format_delete(instance) -> str:
    model_name = instance.__class__.__name__
    return (
        f"🗑 [{model_name}] Deleted\n"
        f"ID: {instance.pk}\n"
        f"Object: {instance}"
    )


def format_update(instance, diff: dict) -> str:
    model_name = instance.__class__.__name__
    changes = "\n".join(f"- {field}: {old} → {new}" for field, (old, new) in diff.items())
    return (
        f"✏️ [{model_name}] Updated\n"
        f"ID: {instance.pk}\n"
        f"Changes:\n{changes}"
    )

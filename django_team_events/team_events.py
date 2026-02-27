from django.db.models.signals import post_delete, post_save, pre_save

SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "access_key"}


class TeamEvents:
    def __init__(
        self,
        notify_on: list,
        include_fields: list = None,
        exclude_fields: list = None,
        template: dict = None,
    ):
        self.notify_on = notify_on
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields
        self.template = template or {}

    def __set_name__(self, owner, name):
        self.name = name
        self._register(owner)

    def _register(self, model):
        pre_save.connect(self._handle_pre_save, sender=model, weak=False)
        post_save.connect(self._handle_post_save, sender=model, weak=False)
        post_delete.connect(self._handle_post_delete, sender=model, weak=False)

    def _handle_pre_save(self, sender, instance, **kwargs):
        if instance.pk:
            try:
                instance._pre_save_snapshot = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                instance._pre_save_snapshot = None
        else:
            instance._pre_save_snapshot = None

    def _handle_post_save(self, sender, instance, created, **kwargs):
        from django_team_events.providers import google_chat

        if created and "create" in self.notify_on:
            from django_team_events.formatter import format_create
            fields = _all_fields(instance)
            fields = _apply_filters(fields, self.include_fields, self.exclude_fields)
            message = _apply_template(self.template, "create", instance, fields) \
                or format_create(instance, fields)
            google_chat.send(message)

        elif not created and "update" in self.notify_on:
            from django_team_events.formatter import format_update
            snapshot = getattr(instance, "_pre_save_snapshot", None)
            diff = _compute_diff(snapshot, instance)
            diff = _apply_filters(diff, self.include_fields, self.exclude_fields)
            if not diff:
                return
            # For update templates, expose current field values for formatting
            fields = _all_fields(instance)
            message = _apply_template(self.template, "update", instance, fields) \
                or format_update(instance, diff)
            google_chat.send(message)

    def _handle_post_delete(self, sender, instance, **kwargs):
        if "delete" not in self.notify_on:
            return

        from django_team_events.formatter import format_delete
        from django_team_events.providers import google_chat

        try:
            fields = _all_fields(instance)
            message = _apply_template(self.template, "delete", instance, fields) \
                or format_delete(instance)
            google_chat.send(message)
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "django-team-events: error handling delete event"
            )


def _all_fields(instance) -> dict:
    result = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.auto_created:
            continue
        result[field.name] = getattr(instance, field.attname)
    return result


def _compute_diff(original, updated) -> dict:
    if original is None:
        return {}

    diff = {}
    for field in updated._meta.concrete_fields:
        if field.primary_key or field.auto_created:
            continue
        old_val = getattr(original, field.attname)
        new_val = getattr(updated, field.attname)
        if old_val != new_val:
            diff[field.name] = (old_val, new_val)
    return diff


def _apply_template(template: dict, action: str, instance, fields: dict):
    """Return formatted template string for action, or None to signal fallback."""
    tmpl = template.get(action)
    if tmpl is None:
        return None
    try:
        return tmpl.format(**fields)
    except (KeyError, AttributeError, TypeError):
        return None


def _apply_filters(fields: dict, include_fields, exclude_fields) -> dict:
    # Step 1: fields already provided (changed or all)
    result = dict(fields)

    # Step 2: remove sensitive fields (unless include_fields explicitly allows them)
    if include_fields is None:
        result = {k: v for k, v in result.items() if k.lower() not in SENSITIVE_FIELDS}

    # Step 3: apply include_fields
    if include_fields is not None:
        result = {k: v for k, v in result.items() if k in include_fields}

    # Step 4: apply exclude_fields
    if exclude_fields is not None:
        result = {k: v for k, v in result.items() if k not in exclude_fields}

    return result

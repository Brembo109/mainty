from datetime import date, datetime
from decimal import Decimal

from django.db.models import signals
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.roles import get_primary_role_label, get_user_code, get_user_display_name
from audit.context import get_current_audit_user, get_current_change_reason

from .models import AuditLog
from .registry import IGNORED_AUDIT_FIELDS, STATUS_LIKE_FIELDS, TRACKED_MODELS


def register_audit_signals():
    for model in TRACKED_MODELS:
        signals.pre_save.connect(cache_original_instance, sender=model, dispatch_uid=f"audit_pre_save_{model.__name__}")
        signals.post_save.connect(write_save_audit_logs, sender=model, dispatch_uid=f"audit_post_save_{model.__name__}")
        signals.pre_delete.connect(write_delete_audit_log, sender=model, dispatch_uid=f"audit_pre_delete_{model.__name__}")
        for field in model._meta.many_to_many:
            signals.m2m_changed.connect(
                write_m2m_audit_logs,
                sender=field.remote_field.through,
                dispatch_uid=f"audit_m2m_{model.__name__}_{field.name}",
            )


def cache_original_instance(sender, instance, **kwargs):
    if not instance.pk:
        instance._audit_original = None
        return
    try:
        instance._audit_original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audit_original = None


def write_save_audit_logs(sender, instance, created, **kwargs):
    user = get_current_audit_user()
    change_reason = getattr(instance, "_audit_change_reason", "") or get_current_change_reason()
    user_snapshot = _build_user_snapshot(user)
    if created:
        AuditLog.objects.create(
            user=user,
            user_display_snapshot=user_snapshot["display"],
            user_role_snapshot=user_snapshot["role"],
            action=AuditLog.ACTION_CREATE,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            object_repr=_truncate(str(instance)),
            old_value="",
            new_value=_build_summary(instance),
            change_reason=change_reason,
        )
        return

    original = getattr(instance, "_audit_original", None)
    if original is None:
        return

    for field in _tracked_fields(sender):
        old_raw = _raw_field_value(original, field)
        new_raw = _raw_field_value(instance, field)
        if old_raw == new_raw:
            continue
        AuditLog.objects.create(
            user=user,
            user_display_snapshot=user_snapshot["display"],
            user_role_snapshot=user_snapshot["role"],
            action=(
                AuditLog.ACTION_STATUS_CHANGE if field.name in STATUS_LIKE_FIELDS else AuditLog.ACTION_UPDATE
            ),
            model_name=sender.__name__,
            object_id=str(instance.pk),
            object_repr=_truncate(str(instance)),
            field_name=field.name,
            old_value=_serialize_field_value(original, field),
            new_value=_serialize_field_value(instance, field),
            change_reason=change_reason,
        )


def write_delete_audit_log(sender, instance, **kwargs):
    user = get_current_audit_user()
    user_snapshot = _build_user_snapshot(user)
    AuditLog.objects.create(
        user=user,
        user_display_snapshot=user_snapshot["display"],
        user_role_snapshot=user_snapshot["role"],
        action=AuditLog.ACTION_DELETE,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        object_repr=_truncate(str(instance)),
        old_value=_build_summary(instance),
        new_value="",
        change_reason=getattr(instance, "_audit_change_reason", "") or get_current_change_reason(),
    )


def write_m2m_audit_logs(sender, instance, action, reverse, model, pk_set, **kwargs):
    if reverse or action not in {"post_add", "post_remove", "post_clear"}:
        return
    if instance.__class__ not in TRACKED_MODELS:
        return

    field = _get_m2m_field_for_sender(instance.__class__, sender)
    if field is None:
        return

    related_queryset = model._default_manager.filter(pk__in=pk_set).order_by("pk") if pk_set else model._default_manager.none()
    if action == "post_add":
        old_value = ""
        new_value = "; ".join(str(obj) for obj in related_queryset)
    elif action == "post_remove":
        old_value = "; ".join(str(obj) for obj in related_queryset)
        new_value = ""
    else:
        old_value = str(_("Alle Zuordnungen entfernt"))
        new_value = ""

    user = get_current_audit_user()
    user_snapshot = _build_user_snapshot(user)
    AuditLog.objects.create(
        user=user,
        user_display_snapshot=user_snapshot["display"],
        user_role_snapshot=user_snapshot["role"],
        action=AuditLog.ACTION_UPDATE,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        object_repr=_truncate(str(instance)),
        field_name=field.name,
        old_value=str(old_value),
        new_value=str(new_value),
        change_reason=getattr(instance, "_audit_change_reason", "") or get_current_change_reason(),
    )


def _tracked_fields(model):
    fields = []
    for field in model._meta.concrete_fields:
        if field.primary_key:
            continue
        if field.name in IGNORED_AUDIT_FIELDS:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        fields.append(field)
    return fields


def _get_m2m_field_for_sender(model, sender):
    for field in model._meta.many_to_many:
        if field.remote_field.through == sender:
            return field
    return None


def _raw_field_value(instance, field):
    if field.many_to_one:
        return getattr(instance, field.attname)
    return field.value_from_object(instance)


def _serialize_field_value(instance, field):
    if field.many_to_one:
        related_pk = getattr(instance, field.attname)
        if related_pk is None:
            return ""
        related_object = getattr(instance, field.name, None)
        if related_object is None or getattr(related_object, "pk", None) != related_pk:
            related_object = field.remote_field.model._default_manager.filter(pk=related_pk).first()
        return str(related_object or related_pk)

    display_method = getattr(instance, f"get_{field.name}_display", None)
    if callable(display_method):
        return str(display_method())

    value = getattr(instance, field.name)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Ja" if value else "Nein"
    if isinstance(value, datetime):
        localized = timezone.localtime(value) if timezone.is_aware(value) else value
        return localized.strftime("%d.%m.%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _build_summary(instance):
    parts = []
    for field in _tracked_fields(instance.__class__):
        serialized = _serialize_field_value(instance, field)
        raw_value = _raw_field_value(instance, field)
        if raw_value in (None, ""):
            continue
        parts.append(f"{field.verbose_name}: {serialized}")
    return "; ".join(parts)


def _truncate(value: str, limit: int = 255) -> str:
    return value[:limit]


def _build_user_snapshot(user):
    if user is None:
        return {"display": "", "role": ""}

    display = get_user_display_name(user)
    user_code = get_user_code(user)
    if user_code:
        display = f"{display} [{user_code}]"
    return {
        "display": display,
        "role": get_primary_role_label(user) or "",
    }

from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import AuditLog
from .registry import get_tracked_model_choices


def get_audit_entries_for_instance(instance, *, limit: int | None = None):
    queryset = AuditLog.objects.select_related("user").filter(
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
    )
    if limit is not None:
        return queryset[:limit]
    return queryset


def get_audit_list_queryset(*, model_name: str = "", user_id: str = "", action: str = "", query: str = ""):
    queryset = AuditLog.objects.select_related("user")
    if model_name:
        queryset = queryset.filter(model_name=model_name)
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if action:
        queryset = queryset.filter(action=action)
    if query:
        queryset = queryset.filter(Q(object_repr__icontains=query) | Q(object_id__icontains=query))
    return queryset


def get_audit_filter_choices():
    user_model = get_user_model()
    return {
        "model_choices": [
            (model_name, label)
            for model_name, label in get_tracked_model_choices()
            if AuditLog.objects.filter(model_name=model_name).exists()
        ],
        "user_choices": user_model.objects.filter(audit_logs__isnull=False)
        .order_by("username")
        .values_list("id", "username")
        .distinct(),
    }

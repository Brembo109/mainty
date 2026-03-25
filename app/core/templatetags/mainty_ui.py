from django import template
from django.utils.translation import gettext_lazy as _

from contracts.services import (
    CONTRACT_STATUS_ACTIVE,
    CONTRACT_STATUS_EXPIRED,
    CONTRACT_STATUS_NONE,
    CONTRACT_STATUS_WARNING,
)
from core.due_dates import (
    DUE_STATUS_INACTIVE,
    DUE_STATUS_OK,
    DUE_STATUS_OVERDUE,
    DUE_STATUS_UNKNOWN,
    DUE_STATUS_WARNING,
)


register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


@register.filter
def due_badge_class(status_code):
    return {
        DUE_STATUS_OK: "text-bg-success",
        DUE_STATUS_WARNING: "text-bg-warning",
        DUE_STATUS_OVERDUE: "text-bg-danger",
        DUE_STATUS_INACTIVE: "text-bg-secondary",
        DUE_STATUS_UNKNOWN: "text-bg-light border",
    }.get(status_code, "text-bg-light border")


@register.filter
def due_row_class(status_code):
    return {
        DUE_STATUS_WARNING: "table-warning",
        DUE_STATUS_OVERDUE: "table-danger",
    }.get(status_code, "")


@register.filter
def asset_badge_class(status_code):
    return {
        "active": "text-bg-success",
        "inactive": "text-bg-secondary",
        "out_of_service": "text-bg-danger",
    }.get(status_code, "text-bg-light border")


@register.filter
def yesno_badge_class(value):
    return "text-bg-success" if value else "text-bg-secondary"


@register.filter
def contract_badge_class(status_code):
    return {
        CONTRACT_STATUS_ACTIVE: "text-bg-success",
        CONTRACT_STATUS_WARNING: "text-bg-warning",
        CONTRACT_STATUS_EXPIRED: "text-bg-danger",
        CONTRACT_STATUS_NONE: "text-bg-secondary",
    }.get(status_code, "text-bg-light border")


@register.filter
def contract_row_class(status_code):
    return {
        CONTRACT_STATUS_WARNING: "table-warning",
        CONTRACT_STATUS_EXPIRED: "table-danger",
    }.get(status_code, "")


@register.filter
def contract_indicator_class(status_code):
    return {
        CONTRACT_STATUS_ACTIVE: "is-active",
        CONTRACT_STATUS_WARNING: "is-warning",
        CONTRACT_STATUS_EXPIRED: "is-expired",
        CONTRACT_STATUS_NONE: "is-none",
    }.get(status_code, "is-none")


@register.filter
def task_badge_class(task):
    if getattr(task, "is_overdue", False) or getattr(task, "status_code", "") == "overdue":
        return "text-bg-danger"
    return {
        "open": "text-bg-secondary",
        "in_progress": "text-bg-primary",
        "done": "text-bg-success",
    }.get(getattr(task, "status", "") or getattr(task, "status_code", ""), "text-bg-light border")


@register.filter
def task_status_label(task):
    if getattr(task, "is_overdue", False) or getattr(task, "status_code", "") == "overdue":
        return _("Überfällig")
    if hasattr(task, "status_label"):
        return task.status_label
    return task.get_status_display()


@register.filter
def task_row_class(task):
    if getattr(task, "is_overdue", False) or getattr(task, "status_code", "") == "overdue":
        return "table-danger"
    if (getattr(task, "status", "") or getattr(task, "status_code", "")) == "in_progress":
        return "table-primary"
    return ""


@register.simple_tag(takes_context=True)
def nav_link_active(context, target: str):
    request = context["request"]
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is None:
        return ""
    current_url_name = resolver_match.view_name or ""
    current_app_name = resolver_match.app_name or ""
    if target.endswith("*"):
        return "active" if current_url_name.startswith(target[:-1]) else ""
    if (
        target == current_app_name
        or current_url_name == target
        or current_url_name.startswith(f"{target}:")
    ):
        return "active"
    return ""

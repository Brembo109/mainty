from django import template

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

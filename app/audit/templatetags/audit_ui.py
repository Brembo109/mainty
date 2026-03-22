from django import template

from audit.models import AuditLog


register = template.Library()


@register.filter
def audit_action_badge_class(action):
    return {
        AuditLog.ACTION_CREATE: "text-bg-success",
        AuditLog.ACTION_UPDATE: "text-bg-primary",
        AuditLog.ACTION_DELETE: "text-bg-danger",
        AuditLog.ACTION_STATUS_CHANGE: "text-bg-warning",
    }.get(action, "text-bg-light border")

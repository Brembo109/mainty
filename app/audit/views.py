from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from core.exports import ListExportMixin, stringify_export_value
from core.ui import count_active_filters

from .models import AuditLog
from .services import get_audit_filter_choices, get_audit_list_queryset


class AuditLogListView(RoleRequiredMixin, ListExportMixin, ListView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
    model = AuditLog
    template_name = "audit/audit_list.html"
    context_object_name = "audit_entries"
    paginate_by = 20
    export_filename_prefix = "audit-trail"
    export_headers = [
        "Zeitpunkt",
        "Benutzer",
        "Aktion",
        "Modell",
        "Objekt-ID",
        "Objekt",
        "Feld",
        "Alter Wert",
        "Neuer Wert",
        "Änderungsgrund",
    ]

    def get_queryset(self):
        return get_audit_list_queryset(
            model_name=self.request.GET.get("model", "").strip(),
            user_id=self.request.GET.get("user", "").strip(),
            action=self.request.GET.get("action", "").strip(),
            query=self.request.GET.get("q", "").strip(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_choices = get_audit_filter_choices()
        active_filter_count = count_active_filters(self.request.GET)
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_model": self.request.GET.get("model", "").strip(),
                "current_user": self.request.GET.get("user", "").strip(),
                "current_action": self.request.GET.get("action", "").strip(),
                "model_choices": filter_choices["model_choices"],
                "user_choices": filter_choices["user_choices"],
                "action_choices": AuditLog.ACTION_CHOICES,
                "result_count": self.get_queryset().count(),
                "active_filter_count": active_filter_count,
                "has_active_filters": active_filter_count > 0,
                "export_urls": self.get_export_urls(),
            }
        )
        return context

    def get_export_queryset(self):
        return list(self.get_queryset())

    def get_export_rows(self, queryset):
        return [
            [
                stringify_export_value(entry.timestamp),
                entry.user_display,
                entry.get_action_display(),
                entry.model_name,
                entry.object_id,
                entry.object_repr,
                entry.field_name,
                entry.old_value,
                entry.new_value,
                entry.change_reason,
            ]
            for entry in queryset
        ]

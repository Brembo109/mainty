from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from core.ui import count_active_filters

from .models import AuditLog
from .services import get_audit_filter_choices, get_audit_list_queryset


class AuditLogListView(RoleRequiredMixin, ListView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
    model = AuditLog
    template_name = "audit/audit_list.html"
    context_object_name = "audit_entries"
    paginate_by = 20

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
            }
        )
        return context

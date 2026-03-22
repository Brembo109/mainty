from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from core.dashboard import build_dashboard_context


class HomeView(TemplateView):
    template_name = "core/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:dashboard")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_dashboard_context())
        return context


class EditorDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)
    template_name = "core/editor_demo.html"


class AdminDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN,)
    template_name = "core/admin_demo.html"

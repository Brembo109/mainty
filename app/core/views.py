from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER


class HomeView(TemplateView):
    template_name = "core/home.html"


class DashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)
    template_name = "core/dashboard.html"


class EditorDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)
    template_name = "core/editor_demo.html"


class AdminDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN,)
    template_name = "core/admin_demo.html"

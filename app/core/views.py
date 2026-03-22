from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from core.dashboard import build_dashboard_context
from core.forms import SystemSettingsForm
from core.models import SystemSettings


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


class SystemSettingsView(RoleRequiredMixin, UpdateView):
    allowed_roles = (ROLE_ADMIN,)
    form_class = SystemSettingsForm
    template_name = "core/settings_form.html"

    def get_object(self, queryset=None):
        return SystemSettings.load()

    def form_valid(self, form):
        messages.success(self.request, _("Systemeinstellungen wurden erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Systemeinstellungen"),
                "page_description": _(
                    "Globale Standardwerte und Branding für neue Wartungs- und Qualifizierungspläne."
                ),
            }
        )
        return context


class EditorDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)
    template_name = "core/editor_demo.html"


class AdminDemoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN,)
    template_name = "core/admin_demo.html"

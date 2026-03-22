from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.translation import gettext_lazy as _

from .roles import has_role, normalize_role_name


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles: tuple[str, ...] = ()
    permission_denied_message = _("Sie haben keine Berechtigung, auf diese Seite zuzugreifen.")

    def get_allowed_roles(self) -> tuple[str, ...]:
        if not self.allowed_roles:
            raise ImproperlyConfigured("RoleRequiredMixin requires allowed_roles.")
        return tuple(normalize_role_name(role_name) for role_name in self.allowed_roles)

    def test_func(self) -> bool:
        user = self.request.user
        if user.is_superuser:
            return True
        return has_role(user, *self.get_allowed_roles())

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()

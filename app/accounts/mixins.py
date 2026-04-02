from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.translation import gettext_lazy as _

from .permissions import user_has_permissions
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
        return has_role(user, *self.get_allowed_roles())

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()


class PermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_permissions: tuple[str, ...] = ()
    require_all_permissions = True
    permission_denied_message = _("Sie haben keine Berechtigung, auf diese Seite zuzugreifen.")

    def get_required_permissions(self) -> tuple[str, ...]:
        if not self.required_permissions:
            raise ImproperlyConfigured("PermissionRequiredMixin requires required_permissions.")
        return tuple(self.required_permissions)

    def test_func(self) -> bool:
        return user_has_permissions(
            self.request.user,
            self.get_required_permissions(),
            require_all=self.require_all_permissions,
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()

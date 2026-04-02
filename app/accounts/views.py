from datetime import timedelta

from axes.models import AccessAttempt
from axes.utils import reset as reset_axes_attempts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from audit.services import get_audit_entries_for_instance
from core.ui import count_active_filters

from .forms import LoginForm, UserCreateForm, UserUpdateForm
from .mixins import PermissionRequiredMixin, RoleRequiredMixin
from .models import UserProfile
from .permissions import (
    AUDIT_VIEW,
    ROLES_MANAGE,
    USERS_MANAGE,
    build_permissions_matrix,
    get_role_columns,
    log_permission_matrix_changes,
    update_group_permissions_from_matrix,
    user_has_permissions,
)
from .roles import ROLE_ADMIN, ROLE_USER, ROLE_VIEWER


User = get_user_model()


def _build_lockout_status_map(users):
    usernames = [user.username for user in users]
    if not usernames:
        return {}

    cooldown_window_start = timezone.now() - timedelta(minutes=settings.AXES_COOLOFF_TIME)
    attempts = (
        AccessAttempt.objects.filter(
            username__in=usernames,
            failures_since_start__gte=settings.AXES_FAILURE_LIMIT,
            attempt_time__gte=cooldown_window_start,
        )
        .order_by("username", "-attempt_time")
    )

    lockout_statuses = {}
    for attempt in attempts:
        status = lockout_statuses.setdefault(
            attempt.username,
            {
                "is_locked": True,
                "failure_count": attempt.failures_since_start,
                "last_attempt": attempt.attempt_time,
                "ip_addresses": [],
            },
        )
        status["failure_count"] = max(status["failure_count"], attempt.failures_since_start)
        status["last_attempt"] = max(status["last_attempt"], attempt.attempt_time)
        if attempt.ip_address and attempt.ip_address not in status["ip_addresses"]:
            status["ip_addresses"].append(attempt.ip_address)

    return lockout_statuses


class MaintyLoginView(LoginView):
    authentication_form = LoginForm
    redirect_authenticated_user = True
    template_name = "accounts/login.html"


class ProfileView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_USER, ROLE_VIEWER)
    template_name = "accounts/profile.html"


class UserManagementMixin(PermissionRequiredMixin):
    required_permissions = USERS_MANAGE


class RoleManagementMixin(PermissionRequiredMixin):
    required_permissions = ROLES_MANAGE


class UserListView(UserManagementMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    sort_options = {
        "name": ("last_name", "first_name", "username"),
        "-name": ("-last_name", "-first_name", "-username"),
        "username": ("username",),
        "-username": ("-username",),
        "role": ("profile__role", "last_name", "first_name", "username"),
        "active": ("-is_active", "last_name", "first_name", "username"),
        "-updated": ("-date_joined",),
    }

    def get_queryset(self):
        sort = self.request.GET.get("sort", "name")
        queryset = User.objects.select_related("profile").order_by(*self.sort_options.get(sort, self.sort_options["name"]))
        query = self.request.GET.get("q", "").strip()
        role = self.request.GET.get("role", "").strip()
        active = self.request.GET.get("active", "").strip()

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(profile__user_code__icontains=query)
            )
        if role:
            queryset = queryset.filter(profile__role=role)
        if active == "active":
            queryset = queryset.filter(is_active=True)
        elif active == "inactive":
            queryset = queryset.filter(is_active=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        managed_users = list(context["users"])
        lockout_statuses = _build_lockout_status_map(managed_users)
        for managed_user in managed_users:
            managed_user.lockout_status = lockout_statuses.get(
                managed_user.username,
                {"is_locked": False, "failure_count": 0, "last_attempt": None, "ip_addresses": []},
            )
        active_filter_count = count_active_filters(self.request.GET)
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_role": self.request.GET.get("role", "").strip(),
                "current_active": self.request.GET.get("active", "").strip(),
                "current_sort": self.request.GET.get("sort", "name"),
                "role_choices": UserProfile.ROLE_CHOICES,
                "result_count": context["paginator"].count if context.get("paginator") else self.get_queryset().count(),
                "active_filter_count": active_filter_count,
                "has_active_filters": active_filter_count > 0,
                "sort_choices": [
                    ("name", _("Name")),
                    ("username", _("Benutzername")),
                    ("role", _("Rolle")),
                    ("active", _("Status aktiv zuerst")),
                    ("-updated", _("Neueste zuerst")),
                ],
            }
        )
        return context


class UserCreateView(UserManagementMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich angelegt."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:user-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Benutzer anlegen"),
                "submit_label": _("Benutzer anlegen"),
                "cancel_url": reverse("accounts:user-list"),
            }
        )
        return context


class UserUpdateView(UserManagementMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"

    def get_queryset(self):
        return User.objects.select_related("profile")

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("accounts:user-edit", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lockout_status"] = _build_lockout_status_map([self.object]).get(
            self.object.username,
            {"is_locked": False, "failure_count": 0, "last_attempt": None, "ip_addresses": []},
        )
        context.update(
            {
                "page_title": _("Benutzer bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("accounts:user-list"),
            }
        )
        if user_has_permissions(self.request.user, AUDIT_VIEW):
            context["audit_entries"] = get_audit_entries_for_instance(self.object, limit=10)
            context["audit_model_name"] = self.object.__class__.__name__
            context["audit_object_id"] = self.object.pk
        return context


class RolePermissionMatrixView(RoleManagementMixin, TemplateView):
    template_name = "accounts/permission_matrix.html"

    def post(self, request, *args, **kwargs):
        changes = update_group_permissions_from_matrix(request.POST)
        log_permission_matrix_changes(request.user, changes)

        if changes:
            messages.success(request, _("Rollen und Rechte wurden erfolgreich aktualisiert."))
        else:
            messages.info(request, _("Es wurden keine Änderungen gespeichert."))
        return redirect("accounts:permission-matrix")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Rollen und Rechte"),
                "role_columns": get_role_columns(),
                "permission_sections": build_permissions_matrix(),
            }
        )
        return context


class UserUnlockView(UserManagementMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs["pk"])
        reset_count = reset_axes_attempts(username=user.username)

        if reset_count:
            messages.success(request, _("Benutzer wurde entsperrt."))
        else:
            messages.info(request, _("Für diesen Benutzer liegt keine aktive Sperre vor."))

        next_url = request.POST.get("next", "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("accounts:user-edit", pk=user.pk)

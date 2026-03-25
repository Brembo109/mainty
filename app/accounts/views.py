from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from audit.services import get_audit_entries_for_instance
from core.ui import count_active_filters

from .forms import LoginForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin
from .models import UserProfile
from .permissions import build_permissions_matrix, get_role_columns, log_permission_matrix_changes, update_group_permissions_from_matrix
from .roles import ROLE_ADMIN, ROLE_USER, ROLE_VIEWER


User = get_user_model()


class MaintyLoginView(LoginView):
    authentication_form = LoginForm
    redirect_authenticated_user = True
    template_name = "accounts/login.html"


class ProfileView(RoleRequiredMixin, TemplateView):
    allowed_roles = (ROLE_ADMIN, ROLE_USER, ROLE_VIEWER)
    template_name = "accounts/profile.html"


class UserManagementMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN,)


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
        context.update(
            {
                "page_title": _("Benutzer bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("accounts:user-list"),
                "audit_entries": get_audit_entries_for_instance(self.object, limit=10),
                "audit_model_name": self.object.__class__.__name__,
                "audit_object_id": self.object.pk,
            }
        )
        return context


class RolePermissionMatrixView(UserManagementMixin, TemplateView):
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

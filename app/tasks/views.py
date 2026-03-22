from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset

from .forms import TaskForm
from .models import Task


class TaskAccessMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)


class TaskEditMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)


class TaskListView(TaskAccessMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    sort_options = {
        "due_date": "due_date",
        "-due_date": "-due_date",
        "title": "title",
        "-title": "-title",
        "priority": "priority",
        "status": "status",
        "responsible_user": "responsible_user__username",
        "asset": "asset__asset_id",
        "-updated_at": "-updated_at",
        "-completed_at": "-completed_at",
    }

    def get_queryset(self):
        queryset = super().get_queryset().select_related("asset", "responsible_user")
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        responsible_user = self.request.GET.get("responsible_user", "").strip()
        asset = self.request.GET.get("asset", "").strip()
        overdue = self.request.GET.get("overdue", "").strip()
        sort = self.request.GET.get("sort", "due_date")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(asset__asset_id__icontains=query)
                | Q(asset__name__icontains=query)
                | Q(responsible_user__username__icontains=query)
            )

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if responsible_user:
            queryset = queryset.filter(responsible_user_id=responsible_user)
        if asset:
            queryset = queryset.filter(asset_id=asset)
        if overdue == "yes":
            queryset = queryset.filter(due_date__lt=timezone.localdate()).exclude(status=Task.STATUS_DONE)
        elif overdue == "no":
            queryset = queryset.exclude(due_date__lt=timezone.localdate(), status__in=[Task.STATUS_OPEN, Task.STATUS_IN_PROGRESS])

        return queryset.order_by(*self._get_ordering(sort))

    def _get_ordering(self, sort):
        ordering = self.sort_options.get(sort, "due_date")
        if sort in {"responsible_user", "asset"}:
            return [ordering, "title"]
        if sort in {"priority", "status"}:
            return [ordering, "due_date", "title"]
        return [ordering]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_status": self.request.GET.get("status", "").strip(),
                "current_priority": self.request.GET.get("priority", "").strip(),
                "current_responsible_user": self.request.GET.get("responsible_user", "").strip(),
                "current_asset": self.request.GET.get("asset", "").strip(),
                "current_overdue": self.request.GET.get("overdue", "").strip(),
                "current_sort": self.request.GET.get("sort", "due_date"),
                "result_count": self.get_queryset().count(),
                "status_choices": Task.STATUS_CHOICES,
                "priority_choices": Task.PRIORITY_CHOICES,
                "responsible_user_choices": self._get_responsible_user_choices(),
                "asset_choices": Asset.objects.order_by("asset_id").values_list("id", "asset_id", "name"),
                "sort_choices": [
                    ("due_date", _("Fälligkeitsdatum aufsteigend")),
                    ("-due_date", _("Fälligkeitsdatum absteigend")),
                    ("title", _("Titel A-Z")),
                    ("-title", _("Titel Z-A")),
                    ("priority", _("Priorität")),
                    ("status", _("Status")),
                    ("responsible_user", _("Verantwortliche Person")),
                    ("asset", _("Anlage")),
                    ("-completed_at", _("Zuletzt abgeschlossen")),
                    ("-updated_at", _("Zuletzt geändert")),
                ],
            }
        )
        return context

    def _get_responsible_user_choices(self):
        queryset = (
            Task.objects.exclude(responsible_user__isnull=True)
            .select_related("responsible_user")
            .order_by("responsible_user__username")
            .values_list("responsible_user_id", "responsible_user__username")
            .distinct()
        )
        return queryset


class TaskDetailView(TaskAccessMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return super().get_queryset().select_related("asset", "responsible_user")


class TaskCreateView(TaskEditMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_initial(self):
        initial = super().get_initial()
        asset_id = self.request.GET.get("asset")
        if asset_id:
            initial["asset"] = asset_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, _("Maßnahme wurde erfolgreich angelegt."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Maßnahme anlegen"),
                "submit_label": _("Maßnahme anlegen"),
                "cancel_url": reverse("tasks:list"),
            }
        )
        return context


class TaskUpdateView(TaskEditMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Maßnahme wurde erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tasks:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Maßnahme bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("tasks:detail", kwargs={"pk": self.object.pk}),
            }
        )
        return context

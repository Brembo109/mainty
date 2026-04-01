from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from audit.services import get_audit_entries_for_instance
from core.exports import ListExportMixin, stringify_export_value
from core.models import SystemSettings
from core.ui import count_active_filters

from .forms import MaintenanceEventForm, MaintenancePlanForm
from .models import MaintenanceEvent, MaintenancePlan


class MaintenanceAccessMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)


class MaintenanceEditMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)


class MaintenancePlanListView(MaintenanceAccessMixin, ListExportMixin, ListView):
    model = MaintenancePlan
    template_name = "maintenance/plan_list.html"
    context_object_name = "plans"
    paginate_by = 10
    export_filename_prefix = "wartungsplaene"
    export_headers = [
        "Anlage",
        "Titel",
        "Intervallwert",
        "Intervall-Einheit",
        "Warnungstage",
        "Verantwortlich",
        "Aktiv",
        "Letztes Ereignis",
        "Nächste Fälligkeit",
        "Fälligkeitsstatus",
        "Notizen",
    ]

    def get_queryset(self):
        queryset = list(super().get_queryset().select_related("asset"))
        query = self.request.GET.get("q", "").strip().lower()
        due_status = self.request.GET.get("due_status", "").strip()
        activity = self.request.GET.get("active", "").strip()
        asset_value = self.request.GET.get("asset", "").strip()
        location = self.request.GET.get("location", "").strip()
        department = self.request.GET.get("department", "").strip()
        sort = self.request.GET.get("sort", "asset")

        if query:
            queryset = [
                plan
                for plan in queryset
                if query in plan.title.lower()
                or query in plan.asset.asset_id.lower()
                or query in plan.asset.name.lower()
                or query in (plan.responsible_person or "").lower()
            ]

        if due_status:
            queryset = [plan for plan in queryset if plan.due_status.code == due_status]
        if activity == "active":
            queryset = [plan for plan in queryset if plan.is_active]
        elif activity == "inactive":
            queryset = [plan for plan in queryset if not plan.is_active]
        if asset_value:
            queryset = [plan for plan in queryset if str(plan.asset_id) == asset_value]
        if location:
            queryset = [plan for plan in queryset if plan.asset.location == location]
        if department:
            queryset = [plan for plan in queryset if plan.asset.department == department]

        return sorted(queryset, key=self._sort_key(sort), reverse=sort.startswith("-"))

    def _sort_key(self, sort):
        key = sort.lstrip("-")
        if key == "title":
            return lambda plan: (plan.title.lower(), plan.asset.asset_id.lower())
        if key == "next_due_date":
            return lambda plan: (plan.next_due_date is None, plan.next_due_date)
        if key == "due_status":
            order = {"ok": 1, "warning": 2, "overdue": 3, "inactive": 4, "unknown": 5}
            return lambda plan: order.get(plan.due_status.code, 99)
        if key == "updated_at":
            return lambda plan: plan.updated_at
        return lambda plan: (plan.asset.asset_id.lower(), plan.title.lower())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assets = MaintenancePlan.objects.select_related("asset").values_list("asset_id", "asset__asset_id", "asset__name").distinct()
        base_assets = MaintenancePlan.objects.select_related("asset")
        active_filter_count = count_active_filters(self.request.GET, ignored_keys={"sort"})
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_due_status": self.request.GET.get("due_status", "").strip(),
                "current_active": self.request.GET.get("active", "").strip(),
                "current_asset": self.request.GET.get("asset", "").strip(),
                "current_location": self.request.GET.get("location", "").strip(),
                "current_department": self.request.GET.get("department", "").strip(),
                "current_sort": self.request.GET.get("sort", "asset"),
                "result_count": context["paginator"].count if context.get("paginator") else len(context["plans"]),
                "active_filter_count": active_filter_count,
                "has_active_filters": active_filter_count > 0,
                "asset_choices": assets,
                "location_choices": base_assets.exclude(asset__location="").order_by("asset__location").values_list("asset__location", flat=True).distinct(),
                "department_choices": base_assets.exclude(asset__department="").order_by("asset__department").values_list("asset__department", flat=True).distinct(),
                "sort_choices": [
                    ("asset", _("Asset")),
                    ("title", _("Titel")),
                    ("next_due_date", _("Nächste Fälligkeit")),
                    ("due_status", _("Fälligkeitsstatus")),
                    ("-updated_at", _("Zuletzt geändert")),
                ],
                "export_urls": self.get_export_urls(),
            }
        )
        return context

    def get_export_queryset(self):
        return list(self.get_queryset())

    def get_export_rows(self, queryset):
        return [
            [
                str(plan.asset),
                plan.title,
                stringify_export_value(plan.interval_value),
                plan.get_interval_unit_display(),
                stringify_export_value(plan.warning_days),
                plan.responsible_person,
                stringify_export_value(plan.is_active),
                stringify_export_value(plan.latest_event.performed_on if plan.latest_event else None),
                stringify_export_value(plan.next_due_date),
                plan.due_status.label,
                plan.notes,
            ]
            for plan in queryset
        ]


class MaintenancePlanDetailView(MaintenanceAccessMixin, DetailView):
    model = MaintenancePlan
    template_name = "maintenance/plan_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return super().get_queryset().select_related("asset")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_history"] = self.object.events.all()
        context["audit_entries"] = get_audit_entries_for_instance(self.object, limit=10)
        context["audit_model_name"] = self.object.__class__.__name__
        context["audit_object_id"] = self.object.pk
        return context


class MaintenancePlanCreateView(MaintenanceEditMixin, CreateView):
    model = MaintenancePlan
    form_class = MaintenancePlanForm
    template_name = "maintenance/plan_form.html"

    def get_initial(self):
        initial = super().get_initial()
        settings = SystemSettings.load()
        asset_id = self.request.GET.get("asset")
        if asset_id:
            initial["asset"] = asset_id
        initial.setdefault("interval_value", settings.default_maintenance_interval_value)
        initial.setdefault("interval_unit", settings.default_maintenance_interval_unit)
        initial.setdefault("warning_days", settings.default_maintenance_warning_days)
        return initial

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsplan wurde erfolgreich angelegt."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("maintenance:plan-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Wartungsplan anlegen"),
                "submit_label": _("Wartungsplan anlegen"),
                "cancel_url": reverse("maintenance:plan-list"),
            }
        )
        return context


class MaintenancePlanUpdateView(MaintenanceEditMixin, UpdateView):
    model = MaintenancePlan
    form_class = MaintenancePlanForm
    template_name = "maintenance/plan_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsplan wurde erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("maintenance:plan-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Wartungsplan bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("maintenance:plan-detail", kwargs={"pk": self.object.pk}),
            }
        )
        return context


class MaintenanceEventCreateView(MaintenanceEditMixin, CreateView):
    model = MaintenanceEvent
    form_class = MaintenanceEventForm
    template_name = "maintenance/event_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.plan = MaintenancePlan.objects.select_related("asset").get(pk=kwargs["plan_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.plan = self.plan
        messages.success(self.request, _("Wartungsereignis wurde erfasst."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("maintenance:plan-detail", kwargs={"pk": self.plan.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "plan": self.plan,
                "page_title": _("Wartungsereignis erfassen"),
                "submit_label": _("Ereignis speichern"),
                "cancel_url": reverse("maintenance:plan-detail", kwargs={"pk": self.plan.pk}),
            }
        )
        return context


class MaintenanceEventUpdateView(MaintenanceEditMixin, UpdateView):
    model = MaintenanceEvent
    form_class = MaintenanceEventForm
    template_name = "maintenance/event_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsereignis wurde aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("maintenance:plan-detail", kwargs={"pk": self.object.plan.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "plan": self.object.plan,
                "page_title": _("Wartungsereignis bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("maintenance:plan-detail", kwargs={"pk": self.object.plan.pk}),
            }
        )
        return context

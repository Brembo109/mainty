from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import PermissionRequiredMixin
from accounts.permissions import (
    ASSETS_ADD,
    ASSETS_CHANGE,
    ASSETS_VIEW,
    AUDIT_VIEW,
    CONTRACTS_VIEW,
    MAINTENANCE_PLAN_VIEW,
    QUALIFICATION_PLAN_VIEW,
    TASKS_VIEW,
    user_has_permissions,
)
from audit.services import get_audit_entries_for_instance
from core.exports import ListExportMixin, stringify_export_value
from core.ui import count_active_filters
from contracts.services import summarize_asset_contract_status

from .forms import AssetForm
from .models import Asset


class AssetAccessMixin(PermissionRequiredMixin):
    required_permissions = ASSETS_VIEW


class AssetCreateAccessMixin(PermissionRequiredMixin):
    required_permissions = ASSETS_ADD


class AssetUpdateAccessMixin(PermissionRequiredMixin):
    required_permissions = ASSETS_CHANGE


class AssetListView(AssetAccessMixin, ListExportMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10
    export_filename_prefix = "geraete"
    export_headers = [
        "Asset-ID",
        "Bezeichnung",
        "Kurzname",
        "Kategorie",
        "Hersteller",
        "Modell",
        "Seriennummer",
        "Standort",
        "Abteilung",
        "Inbetriebnahme",
        "Status",
        "Notizen",
    ]

    sort_options = {
        "asset_id": "asset_id",
        "-asset_id": "-asset_id",
        "name": "name",
        "-name": "-name",
        "commissioning_date": "commissioning_date",
        "-commissioning_date": "-commissioning_date",
        "status": "status",
        "location": "location",
        "department": "department",
        "-updated_at": "-updated_at",
    }

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related("contracts")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        location = self.request.GET.get("location", "").strip()
        department = self.request.GET.get("department", "").strip()
        sort = self.request.GET.get("sort", "asset_id")

        if q:
            queryset = queryset.filter(
                Q(asset_id__icontains=q)
                | Q(name__icontains=q)
                | Q(short_name__icontains=q)
                | Q(category__icontains=q)
                | Q(manufacturer__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(location__icontains=q)
                | Q(department__icontains=q)
            )

        if status:
            queryset = queryset.filter(status=status)
        if location:
            queryset = queryset.filter(location=location)
        if department:
            queryset = queryset.filter(department=department)

        return queryset.order_by(self.sort_options.get(sort, "asset_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for asset in context["assets"]:
            asset.contract_summary = summarize_asset_contract_status(asset)
        filters_source = Asset.objects.all()
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_status": self.request.GET.get("status", "").strip(),
                "current_location": self.request.GET.get("location", "").strip(),
                "current_department": self.request.GET.get("department", "").strip(),
                "current_sort": self.request.GET.get("sort", "asset_id"),
                "status_choices": Asset.STATUS_CHOICES,
                "location_choices": filters_source.exclude(location="").order_by("location").values_list("location", flat=True).distinct(),
                "department_choices": filters_source.exclude(department="").order_by("department").values_list("department", flat=True).distinct(),
                "result_count": self.get_queryset().count(),
                "active_filter_count": count_active_filters(self.request.GET, ignored_keys={"sort"}),
                "has_active_filters": count_active_filters(self.request.GET, ignored_keys={"sort"}) > 0,
                "sort_choices": [
                    ("asset_id", _("Asset-ID aufsteigend")),
                    ("-asset_id", _("Asset-ID absteigend")),
                    ("name", _("Name A-Z")),
                    ("-name", _("Name Z-A")),
                    ("commissioning_date", _("Inbetriebnahme aufsteigend")),
                    ("-commissioning_date", _("Inbetriebnahme absteigend")),
                    ("status", _("Status")),
                    ("location", _("Standort")),
                    ("department", _("Abteilung")),
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
                asset.asset_id,
                asset.name,
                asset.short_name,
                asset.category,
                asset.manufacturer,
                asset.model,
                asset.serial_number,
                asset.location,
                asset.department,
                stringify_export_value(asset.commissioning_date),
                asset.get_status_display(),
                asset.notes,
            ]
            for asset in queryset
        ]


class AssetDetailView(AssetAccessMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["maintenance_plans"] = (
            self.object.maintenance_plans.all()
            if user_has_permissions(user, MAINTENANCE_PLAN_VIEW)
            else []
        )
        context["qualification_plans"] = (
            self.object.qualification_plans.all()
            if user_has_permissions(user, QUALIFICATION_PLAN_VIEW)
            else []
        )
        context["tasks"] = (
            self.object.tasks.select_related("responsible_user").all()
            if user_has_permissions(user, TASKS_VIEW)
            else []
        )
        can_view_contracts = user_has_permissions(user, CONTRACTS_VIEW)
        context["contracts"] = self.object.contracts.all() if can_view_contracts else []
        context["contract_summary"] = summarize_asset_contract_status(self.object) if can_view_contracts else None
        if user_has_permissions(user, AUDIT_VIEW):
            context["audit_entries"] = get_audit_entries_for_instance(self.object, limit=10)
            context["audit_model_name"] = self.object.__class__.__name__
            context["audit_object_id"] = self.object.pk
        return context


class AssetCreateView(AssetCreateAccessMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Anlage wurde erfolgreich angelegt."))
        return super().form_valid(form)

    def get_success_url(self):
        if not user_has_permissions(self.request.user, ASSETS_VIEW):
            return reverse("assets:list")
        return reverse("assets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Anlage anlegen")
        context["submit_label"] = _("Anlage anlegen")
        context["cancel_url"] = reverse("assets:list")
        return context


class AssetUpdateView(AssetUpdateAccessMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"

    def form_valid(self, form):
        messages.success(self.request, _("Anlage wurde erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        if not user_has_permissions(self.request.user, ASSETS_VIEW):
            return reverse("assets:list")
        return reverse("assets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Anlage bearbeiten")
        context["submit_label"] = _("Änderungen speichern")
        context["cancel_url"] = reverse("assets:detail", kwargs={"pk": self.object.pk})
        return context

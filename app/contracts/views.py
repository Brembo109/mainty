from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER, has_role
from audit.services import get_audit_entries_for_instance
from core.exports import ListExportMixin, stringify_export_value
from core.ui import count_active_filters

from .forms import MaintenanceContractForm
from .models import MaintenanceContract


class ContractAccessMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)


class ContractEditMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)


class ContractDeleteMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN,)


class MaintenanceContractListView(ContractAccessMixin, ListExportMixin, ListView):
    model = MaintenanceContract
    template_name = "contracts/contract_list.html"
    context_object_name = "contracts"
    paginate_by = 10
    export_filename_prefix = "vertraege"
    export_headers = [
        "Titel",
        "Vertragsnummer",
        "Auftragsnummer",
        "Dienstleister",
        "Startdatum",
        "Enddatum",
        "Restlaufzeit",
        "Status",
        "Wartungsintervall",
        "Anzahl Assets",
        "Assets",
        "Notizen",
    ]

    def get_queryset(self):
        queryset = list(
            super()
            .get_queryset()
            .prefetch_related("assets")
            .annotate(asset_count=Count("assets", distinct=True))
        )
        query = self.request.GET.get("q", "").strip().lower()
        status = self.request.GET.get("status", "").strip()
        vendor = self.request.GET.get("vendor", "").strip()
        asset_id = self.request.GET.get("asset", "").strip()
        sort = self.request.GET.get("sort", "end_date")

        if query:
            queryset = [
                contract
                for contract in queryset
                if query in contract.title.lower()
                or query in (contract.contract_number or "").lower()
                or query in (contract.order_number or "").lower()
                or query in contract.vendor.lower()
            ]
        if status:
            queryset = [contract for contract in queryset if contract.status.code == status]
        if vendor:
            queryset = [contract for contract in queryset if contract.vendor == vendor]
        if asset_id:
            queryset = [
                contract
                for contract in queryset
                if any(str(asset.pk) == asset_id for asset in contract.assets.all())
            ]

        return sorted(queryset, key=self._sort_key(sort), reverse=sort.startswith("-"))

    def _sort_key(self, sort):
        key = sort.lstrip("-")
        if key == "title":
            return lambda contract: contract.title.lower()
        if key == "vendor":
            return lambda contract: (contract.vendor.lower(), contract.title.lower())
        if key == "status":
            order = {"active": 1, "warning": 2, "expired": 3, "none": 4}
            return lambda contract: order.get(contract.status.code, 99)
        if key == "asset_count":
            return lambda contract: getattr(contract, "asset_count", contract.assets.count())
        if key == "updated_at":
            return lambda contract: contract.updated_at
        return lambda contract: (contract.end_date, contract.title.lower())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_queryset = MaintenanceContract.objects.prefetch_related("assets")
        active_filter_count = count_active_filters(self.request.GET, ignored_keys={"sort"})
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "current_status": self.request.GET.get("status", "").strip(),
                "current_vendor": self.request.GET.get("vendor", "").strip(),
                "current_asset": self.request.GET.get("asset", "").strip(),
                "current_sort": self.request.GET.get("sort", "end_date"),
                "result_count": context["paginator"].count if context.get("paginator") else len(context["contracts"]),
                "active_filter_count": active_filter_count,
                "has_active_filters": active_filter_count > 0,
                "vendor_choices": contract_queryset.exclude(vendor="").order_by("vendor").values_list("vendor", flat=True).distinct(),
                "asset_choices": contract_queryset.values_list("assets__id", "assets__asset_id", "assets__name").exclude(assets__id=None).distinct(),
                "sort_choices": [
                    ("end_date", _("Enddatum")),
                    ("title", _("Titel")),
                    ("vendor", _("Dienstleister")),
                    ("status", _("Status")),
                    ("-asset_count", _("Meiste Assets")),
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
                contract.title,
                contract.contract_number,
                contract.order_number,
                contract.vendor,
                stringify_export_value(contract.start_date),
                stringify_export_value(contract.end_date),
                contract.remaining_runtime_display,
                contract.status.label,
                contract.get_maintenance_frequency_display(),
                stringify_export_value(getattr(contract, "asset_count", contract.assets.count())),
                ", ".join(asset.asset_id for asset in contract.assets.all()),
                contract.notes,
            ]
            for contract in queryset
        ]


class MaintenanceContractDetailView(ContractAccessMixin, DetailView):
    model = MaintenanceContract
    template_name = "contracts/contract_detail.html"
    context_object_name = "contract"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("assets")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["audit_entries"] = get_audit_entries_for_instance(self.object, limit=10)
        context["audit_model_name"] = self.object.__class__.__name__
        context["audit_object_id"] = self.object.pk
        context["can_delete_contract"] = self.request.user.is_superuser or has_role(self.request.user, ROLE_ADMIN)
        return context


class MaintenanceContractCreateView(ContractEditMixin, CreateView):
    model = MaintenanceContract
    form_class = MaintenanceContractForm
    template_name = "contracts/contract_form.html"

    def get_initial(self):
        initial = super().get_initial()
        asset_id = self.request.GET.get("asset")
        if asset_id:
            initial["assets"] = [asset_id]
        return initial

    def form_valid(self, form):
        messages.success(self.request, _("Vertrag wurde erfolgreich angelegt."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Vertrag anlegen"),
                "submit_label": _("Vertrag anlegen"),
                "cancel_url": reverse("contracts:list"),
            }
        )
        return context


class MaintenanceContractUpdateView(ContractEditMixin, UpdateView):
    model = MaintenanceContract
    form_class = MaintenanceContractForm
    template_name = "contracts/contract_form.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("assets")

    def form_valid(self, form):
        messages.success(self.request, _("Vertrag wurde erfolgreich aktualisiert."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Vertrag bearbeiten"),
                "submit_label": _("Änderungen speichern"),
                "cancel_url": reverse("contracts:detail", kwargs={"pk": self.object.pk}),
            }
        )
        return context


class MaintenanceContractDeleteView(ContractDeleteMixin, DeleteView):
    model = MaintenanceContract
    template_name = "contracts/contract_confirm_delete.html"
    context_object_name = "contract"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("assets")

    def form_valid(self, form):
        messages.success(self.request, _("Vertrag wurde erfolgreich gelöscht."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("contracts:list")

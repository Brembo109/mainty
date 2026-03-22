from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER

from .forms import AssetForm
from .models import Asset


class AssetAccessMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER)


class AssetEditAccessMixin(RoleRequiredMixin):
    allowed_roles = (ROLE_ADMIN, ROLE_EDITOR)


class AssetListView(AssetAccessMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10

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
        queryset = super().get_queryset()
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
                "sort_choices": [
                    ("asset_id", "Asset-ID aufsteigend"),
                    ("-asset_id", "Asset-ID absteigend"),
                    ("name", "Name A-Z"),
                    ("-name", "Name Z-A"),
                    ("commissioning_date", "Inbetriebnahme aufsteigend"),
                    ("-commissioning_date", "Inbetriebnahme absteigend"),
                    ("status", "Status"),
                    ("location", "Standort"),
                    ("department", "Abteilung"),
                    ("-updated_at", "Zuletzt geändert"),
                ],
            }
        )
        return context


class AssetDetailView(AssetAccessMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["maintenance_plans"] = self.object.maintenance_plans.all()
        context["qualification_plans"] = self.object.qualification_plans.all()
        return context


class AssetCreateView(AssetEditAccessMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Anlage wurde erfolgreich angelegt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("assets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Anlage anlegen"
        context["submit_label"] = "Anlage anlegen"
        context["cancel_url"] = reverse("assets:list")
        return context


class AssetUpdateView(AssetEditAccessMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Anlage wurde erfolgreich aktualisiert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("assets:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Anlage bearbeiten"
        context["submit_label"] = "Änderungen speichern"
        context["cancel_url"] = reverse("assets:detail", kwargs={"pk": self.object.pk})
        return context

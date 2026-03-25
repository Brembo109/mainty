from django import forms
from django.utils.translation import gettext_lazy as _

from assets.models import Asset

from .models import MaintenanceContract


class MaintenanceContractForm(forms.ModelForm):
    class Meta:
        model = MaintenanceContract
        fields = [
            "title",
            "contract_number",
            "order_number",
            "vendor",
            "start_date",
            "end_date",
            "warning_months",
            "maintenance_frequency",
            "assets",
            "notes",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "assets": forms.SelectMultiple(attrs={"size": 8}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "title": _("Titel"),
            "contract_number": _("Vertragsnummer"),
            "order_number": _("Auftragsnummer"),
            "vendor": _("Dienstleister"),
            "start_date": _("Startdatum"),
            "end_date": _("Enddatum"),
            "warning_months": _("Vorwarnzeit"),
            "maintenance_frequency": _("Wartungsintervall"),
            "assets": _("Zugeordnete Assets"),
            "notes": _("Notizen"),
        }
        help_texts = {
            "contract_number": _("Interne oder externe Referenznummer des Vertrags."),
            "order_number": _("Optional: zugehörige Auftrags- oder Bestellnummer."),
            "warning_months": _("Anzahl Monate vor Vertragsende, ab denen der Vertrag gelb markiert wird."),
            "maintenance_frequency": _("Rein informativ für die vertraglich vereinbarte Servicefrequenz."),
            "assets": _("Ein Vertrag kann mehreren Assets zugeordnet werden."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assets"].queryset = Asset.objects.order_by("asset_id")
        self.fields["assets"].label_from_instance = lambda asset: f"{asset.asset_id} - {asset.name}"
        for field in self.fields.values():
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_contract_number(self):
        return " ".join((self.cleaned_data.get("contract_number") or "").split())

    def clean_order_number(self):
        return " ".join((self.cleaned_data.get("order_number") or "").split())


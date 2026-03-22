from django import forms
from django.utils.translation import gettext_lazy as _

from .models import MaintenanceEvent, MaintenancePlan


class MaintenancePlanForm(forms.ModelForm):
    class Meta:
        model = MaintenancePlan
        fields = [
            "asset",
            "title",
            "interval_value",
            "interval_unit",
            "warning_days",
            "responsible_person",
            "is_active",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "asset": _("Anlage"),
            "interval_value": _("Intervallwert"),
            "interval_unit": _("Intervall-Einheit"),
            "warning_days": _("Warnungstage"),
            "responsible_person": _("Verantwortlich"),
            "is_active": _("Aktiv"),
            "notes": _("Notizen"),
        }
        help_texts = {
            "warning_days": _("Anzahl der Tage vor Fälligkeit, ab denen die Planung als kritisch markiert wird."),
            "is_active": _("Inaktive Pläne werden grau dargestellt und nicht als operative Fälligkeit gewertet."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class MaintenanceEventForm(forms.ModelForm):
    class Meta:
        model = MaintenanceEvent
        fields = ["performed_on", "performed_by", "notes"]
        widgets = {
            "performed_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "performed_on": _("Durchgeführt am"),
            "performed_by": _("Durchgeführt von"),
            "notes": _("Notizen"),
        }
        help_texts = {
            "performed_on": _("Tatsächlicher Durchführungstermin der Wartung."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

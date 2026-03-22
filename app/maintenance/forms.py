from django import forms

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
        help_texts = {
            "warning_days": "Anzahl der Tage vor Faelligkeit, ab denen die Planung als kritisch markiert wird.",
            "is_active": "Inaktive Plaene werden grau dargestellt und nicht als operative Faelligkeit gewertet.",
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
        help_texts = {
            "performed_on": "Tatsaechlicher Durchfuehrungstermin der Wartung.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

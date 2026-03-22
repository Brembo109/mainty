from django import forms
from django.utils.translation import gettext_lazy as _

from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            "default_maintenance_warning_days",
            "default_maintenance_interval_value",
            "default_maintenance_interval_unit",
            "default_qualification_warning_days",
            "default_qualification_interval_value",
            "default_qualification_interval_unit",
        ]
        labels = {
            "default_maintenance_warning_days": _("Warnungstage"),
            "default_maintenance_interval_value": _("Intervallwert"),
            "default_maintenance_interval_unit": _("Intervall-Einheit"),
            "default_qualification_warning_days": _("Warnungstage"),
            "default_qualification_interval_value": _("Intervallwert"),
            "default_qualification_interval_unit": _("Intervall-Einheit"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

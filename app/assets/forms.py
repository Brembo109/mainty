from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "asset_id",
            "name",
            "short_name",
            "category",
            "manufacturer",
            "model",
            "serial_number",
            "location",
            "department",
            "commissioning_date",
            "status",
            "notes",
        ]
        widgets = {
            "commissioning_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "name": _("Bezeichnung"),
            "commissioning_date": _("Inbetriebnahme"),
        }
        help_texts = {
            "asset_id": _("Eindeutige interne Kennung des Assets."),
            "status": _("Steuert den operativen Zustand des Assets ohne Löschworkflow."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                existing_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_class} form-control".strip()

        self.fields["notes"].widget.attrs["placeholder"] = _("Freitext für interne Hinweise")

from django import forms

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
        help_texts = {
            "asset_id": "Eindeutige interne Kennung des Assets.",
            "status": "Steuert den operativen Zustand des Assets ohne Loeschworkflow.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                existing_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_class} form-control".strip()

        self.fields["notes"].widget.attrs["placeholder"] = "Freitext fuer interne Hinweise"

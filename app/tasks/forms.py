from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from assets.models import Asset

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "asset",
            "due_date",
            "priority",
            "status",
            "responsible_user",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "title": _("Titel"),
            "description": _("Beschreibung"),
            "asset": _("Anlage"),
            "due_date": _("Fällig am"),
            "priority": _("Priorität"),
            "status": _("Status"),
            "responsible_user": _("Verantwortliche Person"),
        }
        help_texts = {
            "asset": _("Optional mit einer Anlage verknüpfen."),
            "due_date": _("Optionales Zieldatum für die Maßnahme."),
            "status": _("Beim Status 'Erledigt' wird der Abschlusszeitpunkt automatisch gesetzt."),
            "responsible_user": _("Optional einer Benutzerin oder einem Benutzer zuweisen."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_model = get_user_model()

        self.fields["asset"].queryset = Asset.objects.order_by("asset_id")
        self.fields["asset"].required = False
        self.fields["asset"].empty_label = _("Keine Anlage")

        self.fields["responsible_user"].queryset = user_model.objects.order_by("username")
        self.fields["responsible_user"].required = False
        self.fields["responsible_user"].empty_label = _("Niemand zugewiesen")

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

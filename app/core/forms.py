from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    company_logo = forms.ImageField(
        required=False,
        label=_("Firmenlogo"),
        help_text=_("Optionales Firmenlogo für Login-Seite und Kopfbereich."),
        validators=[FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "gif", "webp"])],
    )

    class Meta:
        model = SystemSettings
        fields = [
            "company_logo",
            "default_maintenance_warning_days",
            "default_maintenance_interval_value",
            "default_maintenance_interval_unit",
            "default_qualification_warning_days",
            "default_qualification_interval_value",
            "default_qualification_interval_unit",
        ]
        labels = {
            "company_logo": _("Firmenlogo"),
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

        self.fields["company_logo"].widget = forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": "image/*"}
        )

    def clean_company_logo(self):
        logo = self.cleaned_data.get("company_logo")
        if logo and getattr(logo, "size", 0) > 2 * 1024 * 1024:
            raise forms.ValidationError(_("Das Firmenlogo darf maximal 2 MB groß sein."))
        return logo

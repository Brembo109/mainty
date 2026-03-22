from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from .models import SystemSettings
from .runtime import normalize_allowed_hosts, normalize_csrf_trusted_origins, validate_allowed_host, validate_csrf_origin


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
            "app_public_url",
            "allowed_hosts",
            "csrf_trusted_origins",
            "force_https",
            "debug_mode",
        ]
        labels = {
            "company_logo": _("Firmenlogo"),
            "default_maintenance_warning_days": _("Warnungstage"),
            "default_maintenance_interval_value": _("Intervallwert"),
            "default_maintenance_interval_unit": _("Intervall-Einheit"),
            "default_qualification_warning_days": _("Warnungstage"),
            "default_qualification_interval_value": _("Intervallwert"),
            "default_qualification_interval_unit": _("Intervall-Einheit"),
            "app_public_url": _("Öffentliche URL"),
            "allowed_hosts": _("Allowed Hosts"),
            "csrf_trusted_origins": _("CSRF Trusted Origins"),
            "force_https": _("HTTPS erzwingen"),
            "debug_mode": _("Debug-Modus"),
        }
        help_texts = {
            "app_public_url": _("Vollständige öffentliche URL der Anwendung, z. B. https://mainty.example.com"),
            "allowed_hosts": _("Kommagetrennte Hostnamen für den Zugriff über Reverse Proxy oder Tunnel."),
            "csrf_trusted_origins": _("Kommagetrennte Origins inklusive Schema, z. B. https://mainty.example.com"),
            "force_https": _("Leitet HTTP-Anfragen auf HTTPS um, wenn die Anwendung hinter einem Proxy öffentlich erreichbar ist."),
            "debug_mode": _("Nur für technische Fehlersuche aktivieren. Nicht für den Regelbetrieb empfohlen."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

            if name in {"allowed_hosts", "csrf_trusted_origins"}:
                field.widget = forms.Textarea(attrs={"class": "form-control", "rows": 2})

        self.fields["company_logo"].widget = forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": "image/*"}
        )

    def clean_company_logo(self):
        logo = self.cleaned_data.get("company_logo")
        if logo and getattr(logo, "size", 0) > 2 * 1024 * 1024:
            raise forms.ValidationError(_("Das Firmenlogo darf maximal 2 MB groß sein."))
        return logo

    def clean_allowed_hosts(self):
        raw_value = self.cleaned_data.get("allowed_hosts", "")
        hosts = normalize_allowed_hosts(raw_value)
        for host in hosts:
            try:
                validate_allowed_host(host)
            except ValueError as exc:
                raise forms.ValidationError(str(exc)) from exc
        return ", ".join(hosts)

    def clean_csrf_trusted_origins(self):
        raw_value = self.cleaned_data.get("csrf_trusted_origins", "")
        origins = normalize_csrf_trusted_origins(raw_value)
        for origin in origins:
            try:
                validate_csrf_origin(origin)
            except ValueError as exc:
                raise forms.ValidationError(str(exc)) from exc
        return ", ".join(origins)

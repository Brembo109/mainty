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
            "notifications_enabled",
            "notification_from_email",
            "send_upcoming_reminders",
            "send_overdue_reminders",
            "send_daily_digest",
            "send_weekly_digest",
            "maintenance_upcoming_days",
            "qualification_upcoming_days",
            "overdue_escalation_days",
            "only_notify_once_per_status",
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
            "notifications_enabled": _("Benachrichtigungen aktiviert"),
            "notification_from_email": _("Absender E-Mail"),
            "send_upcoming_reminders": _("Erinnerungen vor Fälligkeit senden"),
            "send_overdue_reminders": _("Überfällige Einträge melden"),
            "send_daily_digest": _("Tägliche Zusammenfassung senden"),
            "send_weekly_digest": _("Wöchentliche Zusammenfassung senden"),
            "maintenance_upcoming_days": _("Vorlaufzeit Wartung in Tagen"),
            "qualification_upcoming_days": _("Vorlaufzeit Qualifizierung in Tagen"),
            "overdue_escalation_days": _("Eskalation bei Überfälligkeit ab Tagen"),
            "only_notify_once_per_status": _("Nur einmal pro Status benachrichtigen"),
            "app_public_url": _("Öffentliche URL"),
            "allowed_hosts": _("Allowed Hosts"),
            "csrf_trusted_origins": _("CSRF Trusted Origins"),
            "force_https": _("HTTPS erzwingen"),
            "debug_mode": _("Debug-Modus"),
        }
        help_texts = {
            "app_public_url": _("Vollständige öffentliche URL der Anwendung, z. B. https://mainty.example.com"),
            "notifications_enabled": _(
                "Aktiviert den E-Mail-Versand für Erinnerungen und Zusammenfassungen."
            ),
            "notification_from_email": _(
                "Optionaler Absender für Reminder-E-Mails. Wenn leer, wird DEFAULT_FROM_EMAIL verwendet."
            ),
            "send_upcoming_reminders": _("Sendet Erinnerungen für bald fällige Wartungen und Qualifizierungen."),
            "send_overdue_reminders": _("Sendet Eskalationen für überfällige Wartungen und Qualifizierungen."),
            "send_daily_digest": _("Aktiviert die tägliche E-Mail-Zusammenfassung relevanter Einträge."),
            "send_weekly_digest": _("Aktiviert die wöchentliche E-Mail-Zusammenfassung relevanter Einträge."),
            "maintenance_upcoming_days": _("Anzahl Tage vor Fälligkeit für Wartungs-Erinnerungen."),
            "qualification_upcoming_days": _("Anzahl Tage vor Fälligkeit für Qualifizierungs-Erinnerungen."),
            "overdue_escalation_days": _(
                "Überfällige Einträge werden erst ab dieser Anzahl Tagen gemeldet. 0 bedeutet sofort."
            ),
            "only_notify_once_per_status": _(
                "Wenn aktiviert, wird pro Objekt und Status nur eine Benachrichtigung gesendet."
            ),
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

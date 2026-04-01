from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.roles import get_user_display_with_role
from .registry import IGNORED_AUDIT_FIELDS, get_tracked_model_map


class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_STATUS_CHANGE = "status_change"

    ACTION_CHOICES = [
        (ACTION_CREATE, _("Angelegt")),
        (ACTION_UPDATE, _("Aktualisiert")),
        (ACTION_DELETE, _("Gelöscht")),
        (ACTION_STATUS_CHANGE, _("Statuswechsel")),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Zeitpunkt"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("Benutzer"),
    )
    user_display_snapshot = models.CharField(max_length=255, blank=True, verbose_name=_("Benutzeranzeige"))
    user_role_snapshot = models.CharField(max_length=50, blank=True, verbose_name=_("Benutzerrolle"))
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name=_("Aktion"))
    model_name = models.CharField(max_length=100, db_index=True, verbose_name=_("Modell"))
    object_id = models.CharField(max_length=64, db_index=True, verbose_name=_("Objekt-ID"))
    object_repr = models.CharField(max_length=255, verbose_name=_("Objekt"))
    field_name = models.CharField(max_length=100, blank=True, verbose_name=_("Feld"))
    old_value = models.TextField(blank=True, verbose_name=_("Alter Wert"))
    new_value = models.TextField(blank=True, verbose_name=_("Neuer Wert"))
    change_reason = models.TextField(blank=True, verbose_name=_("Änderungsgrund"))

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["timestamp"]),
        ]
        verbose_name = _("Audit-Eintrag")
        verbose_name_plural = _("Audit-Einträge")

    def __str__(self) -> str:
        return f"{self.model_name} {self.object_id} {self.get_action_display()}"

    @property
    def user_display(self) -> str:
        if self.user_display_snapshot:
            if self.user_role_snapshot:
                return f"{self.user_display_snapshot} - {self.user_role_snapshot}"
            return self.user_display_snapshot
        return get_user_display_with_role(self.user) if self.user else str(_("System"))

    @property
    def model_label(self) -> str:
        model = get_tracked_model_map().get(self.model_name)
        if model is None:
            return self.model_name
        return str(model._meta.verbose_name.title())

    @property
    def field_label(self) -> str:
        if not self.field_name:
            return ""
        model = get_tracked_model_map().get(self.model_name)
        if model is None:
            return self.field_name
        try:
            field = model._meta.get_field(self.field_name)
        except Exception:
            return self.field_name
        return str(field.verbose_name)

    @property
    def old_value_display(self) -> str:
        return self._format_summary_value(self.old_value)

    @property
    def new_value_display(self) -> str:
        return self._format_summary_value(self.new_value)

    def _format_summary_value(self, value: str) -> str:
        if not value or self.field_name:
            return value

        model = get_tracked_model_map().get(self.model_name)
        if model is None:
            return value

        parts = []
        for item in value.split("; "):
            if ": " not in item:
                parts.append(item)
                continue
            field_name, field_value = item.split(": ", 1)
            if field_name in IGNORED_AUDIT_FIELDS:
                continue
            try:
                field = model._meta.get_field(field_name)
            except Exception:
                label = field_name
            else:
                label = str(field.verbose_name)
            parts.append(f"{label}: {field_value}")
        return "; ".join(parts)

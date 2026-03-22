from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


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
        return self.user.username if self.user else str(_("System"))

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class NotificationLog(TimeStampedModel):
    TYPE_UPCOMING = "upcoming"
    TYPE_OVERDUE = "overdue"
    TYPE_DIGEST_DAILY = "digest_daily"
    TYPE_DIGEST_WEEKLY = "digest_weekly"

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    NOTIFICATION_TYPE_CHOICES = [
        (TYPE_UPCOMING, _("Erinnerung vor Fälligkeit")),
        (TYPE_OVERDUE, _("Überfälligkeits-Eskalation")),
        (TYPE_DIGEST_DAILY, _("Tägliche Zusammenfassung")),
        (TYPE_DIGEST_WEEKLY, _("Wöchentliche Zusammenfassung")),
    ]
    STATUS_CHOICES = [
        (STATUS_SUCCESS, _("Erfolgreich")),
        (STATUS_FAILED, _("Fehlgeschlagen")),
    ]

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name=_("Typ"))
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Objekttyp"),
    )
    object_id = models.CharField(max_length=64, blank=True, verbose_name=_("Objekt-ID"))
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name=_("Empfänger"),
    )
    recipient_email = models.EmailField(verbose_name=_("Empfänger E-Mail"))
    subject = models.CharField(max_length=255, blank=True, verbose_name=_("Betreff"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS, verbose_name=_("Status"))
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Gesendet am"))
    period_key = models.CharField(max_length=32, blank=True, verbose_name=_("Periodenschlüssel"))
    error_message = models.TextField(blank=True, verbose_name=_("Fehlermeldung"))

    class Meta:
        ordering = ["-sent_at", "-id"]
        verbose_name = _("Benachrichtigungsprotokoll")
        verbose_name_plural = _("Benachrichtigungsprotokolle")

    def __str__(self) -> str:
        return f"{self.get_notification_type_display()} -> {self.recipient_email}"

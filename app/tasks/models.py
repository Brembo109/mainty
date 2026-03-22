from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from assets.models import Asset
from core.models import TimeStampedModel


class Task(TimeStampedModel):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, _("Niedrig")),
        (PRIORITY_MEDIUM, _("Mittel")),
        (PRIORITY_HIGH, _("Hoch")),
    ]

    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"

    STATUS_CHOICES = [
        (STATUS_OPEN, _("Offen")),
        (STATUS_IN_PROGRESS, _("In Bearbeitung")),
        (STATUS_DONE, _("Erledigt")),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name=_("Asset"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Titel"))
    description = models.TextField(blank=True, verbose_name=_("Beschreibung"))
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Faellig am"))
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name=_("Prioritaet"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        verbose_name=_("Status"),
    )
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name=_("Verantwortlicher Benutzer"),
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Abgeschlossen am"))

    class Meta:
        ordering = ["due_date", "-created_at"]
        verbose_name = _("Aufgabe")
        verbose_name_plural = _("Aufgaben")

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.status != self.STATUS_DONE
            and self.due_date < timezone.localdate()
        )

    def clean(self):
        super().clean()
        if self.completed_at and self.status != self.STATUS_DONE:
            raise ValidationError(
                {"completed_at": _("Abschlusszeitpunkt ist nur für Aufgaben mit dem Status 'Erledigt' zulässig.")}
            )

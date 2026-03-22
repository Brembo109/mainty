from django.db import models
from django.utils.translation import gettext_lazy as _

from assets.models import Asset
from core.due_dates import add_interval, calculate_due_status
from core.models import TimeStampedModel


class QualificationPlan(TimeStampedModel):
    INTERVAL_DAYS = "days"
    INTERVAL_WEEKS = "weeks"
    INTERVAL_MONTHS = "months"
    INTERVAL_YEARS = "years"

    INTERVAL_UNIT_CHOICES = [
        (INTERVAL_DAYS, _("Tage")),
        (INTERVAL_WEEKS, _("Wochen")),
        (INTERVAL_MONTHS, _("Monate")),
        (INTERVAL_YEARS, _("Jahre")),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="qualification_plans",
        verbose_name=_("Asset"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Titel"))
    interval_value = models.PositiveIntegerField(verbose_name=_("Intervallwert"))
    interval_unit = models.CharField(
        max_length=10,
        choices=INTERVAL_UNIT_CHOICES,
        verbose_name=_("Intervall-Einheit"),
    )
    warning_days = models.PositiveIntegerField(default=0, verbose_name=_("Warnungstage"))
    responsible_person = models.CharField(max_length=255, blank=True, verbose_name=_("Verantwortlich"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktiv"))
    notes = models.TextField(blank=True, verbose_name=_("Notizen"))

    class Meta:
        ordering = ["asset__asset_id", "title"]
        verbose_name = _("Qualifizierungsplan")
        verbose_name_plural = _("Qualifizierungsplaene")

    def __str__(self) -> str:
        return f"{self.asset.asset_id} - {self.title}"

    @property
    def latest_event(self):
        return self.events.order_by("-performed_on", "-pk").first()

    @property
    def base_date(self):
        latest_event = self.latest_event
        if latest_event is not None:
            return latest_event.performed_on
        return self.asset.commissioning_date

    @property
    def next_due_date(self):
        if self.base_date is None:
            return None
        return add_interval(self.base_date, self.interval_value, self.interval_unit)

    @property
    def due_status(self):
        return calculate_due_status(
            next_due_date=self.next_due_date,
            warning_days=self.warning_days,
            is_active=self.is_active,
        )


class QualificationEvent(TimeStampedModel):
    plan = models.ForeignKey(
        QualificationPlan,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Qualifizierungsplan"),
    )
    performed_on = models.DateField(verbose_name=_("Durchgefuehrt am"))
    performed_by = models.CharField(max_length=255, blank=True, verbose_name=_("Durchgefuehrt von"))
    notes = models.TextField(blank=True, verbose_name=_("Notizen"))

    class Meta:
        ordering = ["-performed_on", "-id"]
        verbose_name = _("Qualifizierungsereignis")
        verbose_name_plural = _("Qualifizierungsereignisse")

    def __str__(self) -> str:
        return f"{self.plan.title} - {self.performed_on:%Y-%m-%d}"

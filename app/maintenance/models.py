from django.db import models

from assets.models import Asset
from core.due_dates import add_interval, calculate_due_status
from core.models import TimeStampedModel


class MaintenancePlan(TimeStampedModel):
    INTERVAL_DAYS = "days"
    INTERVAL_WEEKS = "weeks"
    INTERVAL_MONTHS = "months"
    INTERVAL_YEARS = "years"

    INTERVAL_UNIT_CHOICES = [
        (INTERVAL_DAYS, "Tage"),
        (INTERVAL_WEEKS, "Wochen"),
        (INTERVAL_MONTHS, "Monate"),
        (INTERVAL_YEARS, "Jahre"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="maintenance_plans",
        verbose_name="Asset",
    )
    title = models.CharField(max_length=255, verbose_name="Titel")
    interval_value = models.PositiveIntegerField(verbose_name="Intervallwert")
    interval_unit = models.CharField(
        max_length=10,
        choices=INTERVAL_UNIT_CHOICES,
        verbose_name="Intervall-Einheit",
    )
    warning_days = models.PositiveIntegerField(default=0, verbose_name="Warnungstage")
    responsible_person = models.CharField(max_length=255, blank=True, verbose_name="Verantwortlich")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    notes = models.TextField(blank=True, verbose_name="Notizen")

    class Meta:
        ordering = ["asset__asset_id", "title"]
        verbose_name = "Wartungsplan"
        verbose_name_plural = "Wartungsplaene"

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


class MaintenanceEvent(TimeStampedModel):
    plan = models.ForeignKey(
        MaintenancePlan,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Wartungsplan",
    )
    performed_on = models.DateField(verbose_name="Durchgefuehrt am")
    performed_by = models.CharField(max_length=255, blank=True, verbose_name="Durchgefuehrt von")
    notes = models.TextField(blank=True, verbose_name="Notizen")

    class Meta:
        ordering = ["-performed_on", "-id"]
        verbose_name = "Wartungsereignis"
        verbose_name_plural = "Wartungsereignisse"

    def __str__(self) -> str:
        return f"{self.plan.title} - {self.performed_on:%Y-%m-%d}"

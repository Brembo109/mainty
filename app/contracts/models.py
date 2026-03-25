from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from assets.models import Asset
from core.models import TimeStampedModel

from .services import calculate_contract_status, get_contract_remaining_runtime_display


class MaintenanceContract(TimeStampedModel):
    FREQUENCY_ANNUAL = "annual"
    FREQUENCY_SEMI_ANNUAL = "semi_annual"
    FREQUENCY_QUARTERLY = "quarterly"
    FREQUENCY_OTHER = "other"

    MAINTENANCE_FREQUENCY_CHOICES = [
        (FREQUENCY_ANNUAL, _("Jährlich")),
        (FREQUENCY_SEMI_ANNUAL, _("Halbjährlich")),
        (FREQUENCY_QUARTERLY, _("Quartalsweise")),
        (FREQUENCY_OTHER, _("Sonstiges")),
    ]

    title = models.CharField(max_length=255, verbose_name=_("Titel"))
    contract_number = models.CharField(max_length=100, blank=True, verbose_name=_("Vertragsnummer"))
    order_number = models.CharField(max_length=100, blank=True, verbose_name=_("Auftragsnummer"))
    vendor = models.CharField(max_length=255, verbose_name=_("Dienstleister"))
    start_date = models.DateField(verbose_name=_("Startdatum"))
    end_date = models.DateField(verbose_name=_("Enddatum"))
    warning_months = models.PositiveIntegerField(default=3, verbose_name=_("Vorwarnzeit in Monaten"))
    maintenance_frequency = models.CharField(
        max_length=20,
        choices=MAINTENANCE_FREQUENCY_CHOICES,
        default=FREQUENCY_ANNUAL,
        verbose_name=_("Wartungsintervall"),
    )
    assets = models.ManyToManyField(
        Asset,
        related_name="contracts",
        blank=True,
        verbose_name=_("Assets"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notizen"))

    class Meta:
        ordering = ["end_date", "title"]
        verbose_name = _("Wartungsvertrag")
        verbose_name_plural = _("Wartungsverträge")

    def __str__(self) -> str:
        if self.contract_number:
            return f"{self.title} ({self.contract_number})"
        return self.title

    @property
    def status(self):
        return calculate_contract_status(end_date=self.end_date, warning_months=self.warning_months)

    @property
    def remaining_runtime_display(self) -> str:
        return get_contract_remaining_runtime_display(end_date=self.end_date)

    def clean(self):
        super().clean()
        self.contract_number = (self.contract_number or "").strip()
        self.order_number = (self.order_number or "").strip()
        self.vendor = (self.vendor or "").strip()
        self.title = (self.title or "").strip()
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": _("Das Enddatum darf nicht vor dem Startdatum liegen.")})


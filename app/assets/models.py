from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class Asset(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_OUT_OF_SERVICE = "out_of_service"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, _("Aktiv")),
        (STATUS_INACTIVE, _("Inaktiv")),
        (STATUS_OUT_OF_SERVICE, _("Ausser Betrieb")),
    ]

    asset_id = models.CharField(max_length=50, unique=True, verbose_name=_("Asset-ID"))
    name = models.CharField(max_length=255, verbose_name=_("Bezeichnung"))
    short_name = models.CharField(max_length=100, blank=True, verbose_name=_("Kurzname"))
    category = models.CharField(max_length=100, blank=True, verbose_name=_("Kategorie"))
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name=_("Hersteller"))
    model = models.CharField(max_length=100, blank=True, verbose_name=_("Modell"))
    serial_number = models.CharField(max_length=100, blank=True, verbose_name=_("Seriennummer"))
    location = models.CharField(max_length=100, blank=True, verbose_name=_("Standort"))
    department = models.CharField(max_length=100, blank=True, verbose_name=_("Abteilung"))
    commissioning_date = models.DateField(null=True, blank=True, verbose_name=_("Inbetriebnahme"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_("Status"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notizen"))

    class Meta:
        ordering = ["asset_id"]
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")

    def __str__(self) -> str:
        return f"{self.asset_id} - {self.name}"

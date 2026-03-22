from django.db import models

from core.models import TimeStampedModel


class Asset(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_OUT_OF_SERVICE = "out_of_service"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktiv"),
        (STATUS_INACTIVE, "Inaktiv"),
        (STATUS_OUT_OF_SERVICE, "Ausser Betrieb"),
    ]

    asset_id = models.CharField(max_length=50, unique=True, verbose_name="Asset-ID")
    name = models.CharField(max_length=255, verbose_name="Bezeichnung")
    short_name = models.CharField(max_length=100, blank=True, verbose_name="Kurzname")
    category = models.CharField(max_length=100, blank=True, verbose_name="Kategorie")
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name="Hersteller")
    model = models.CharField(max_length=100, blank=True, verbose_name="Modell")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Seriennummer")
    location = models.CharField(max_length=100, blank=True, verbose_name="Standort")
    department = models.CharField(max_length=100, blank=True, verbose_name="Abteilung")
    commissioning_date = models.DateField(null=True, blank=True, verbose_name="Inbetriebnahme")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name="Status",
    )
    notes = models.TextField(blank=True, verbose_name="Notizen")

    class Meta:
        ordering = ["asset_id"]
        verbose_name = "Asset"
        verbose_name_plural = "Assets"

    def __str__(self) -> str:
        return f"{self.asset_id} - {self.name}"

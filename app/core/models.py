from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.intervals import INTERVAL_DAYS, INTERVAL_MONTHS, INTERVAL_UNIT_CHOICES


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        abstract = True


class SystemSettings(TimeStampedModel):
    singleton_enforcer = models.BooleanField(default=True, editable=False, unique=True)
    default_maintenance_warning_days = models.PositiveIntegerField(
        default=7,
        verbose_name=_("Standard Warnungstage Wartung"),
    )
    default_maintenance_interval_value = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Standard Intervallwert Wartung"),
    )
    default_maintenance_interval_unit = models.CharField(
        max_length=10,
        choices=INTERVAL_UNIT_CHOICES,
        default=INTERVAL_DAYS,
        verbose_name=_("Standard Intervall-Einheit Wartung"),
    )
    default_qualification_warning_days = models.PositiveIntegerField(
        default=14,
        verbose_name=_("Standard Warnungstage Qualifizierung"),
    )
    default_qualification_interval_value = models.PositiveIntegerField(
        default=12,
        verbose_name=_("Standard Intervallwert Qualifizierung"),
    )
    default_qualification_interval_unit = models.CharField(
        max_length=10,
        choices=INTERVAL_UNIT_CHOICES,
        default=INTERVAL_MONTHS,
        verbose_name=_("Standard Intervall-Einheit Qualifizierung"),
    )

    class Meta:
        verbose_name = _("Systemeinstellung")
        verbose_name_plural = _("Systemeinstellungen")

    def __str__(self) -> str:
        return str(_("Systemeinstellungen"))

    def clean(self):
        super().clean()
        if not self.singleton_enforcer:
            raise ValidationError({"singleton_enforcer": _("Dieser Wert darf nicht geändert werden.")})

    def save(self, *args, **kwargs):
        self.pk = 1
        self.singleton_enforcer = True
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1, defaults={"singleton_enforcer": True})[0]

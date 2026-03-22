from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.intervals import INTERVAL_DAYS, INTERVAL_MONTHS, INTERVAL_UNIT_CHOICES


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        abstract = True


def default_allowed_hosts() -> str:
    return ", ".join(getattr(settings, "ALLOWED_HOSTS", []))


def default_csrf_trusted_origins() -> str:
    return ", ".join(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))


def default_force_https() -> bool:
    return bool(getattr(settings, "SECURE_SSL_REDIRECT", False))


def default_debug_mode() -> bool:
    return bool(getattr(settings, "DEBUG", False))


class SystemSettings(TimeStampedModel):
    singleton_enforcer = models.BooleanField(default=True, editable=False, unique=True)
    company_logo = models.ImageField(
        upload_to="branding/",
        blank=True,
        verbose_name=_("Firmenlogo"),
    )
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
    app_public_url = models.URLField(
        blank=True,
        verbose_name=_("Öffentliche URL"),
    )
    allowed_hosts = models.TextField(
        blank=True,
        default=default_allowed_hosts,
        verbose_name=_("Allowed Hosts"),
    )
    csrf_trusted_origins = models.TextField(
        blank=True,
        default=default_csrf_trusted_origins,
        verbose_name=_("CSRF Trusted Origins"),
    )
    force_https = models.BooleanField(
        default=default_force_https,
        verbose_name=_("HTTPS erzwingen"),
    )
    debug_mode = models.BooleanField(
        default=default_debug_mode,
        verbose_name=_("Debug-Modus"),
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
        from core.runtime import clear_app_settings_cache

        old_logo_name = ""
        if self.pk:
            old_instance = type(self).objects.filter(pk=self.pk).only("company_logo").first()
            if old_instance and old_instance.company_logo:
                old_logo_name = old_instance.company_logo.name

        self.pk = 1
        self.singleton_enforcer = True
        result = super().save(*args, **kwargs)

        new_logo_name = self.company_logo.name if self.company_logo else ""
        if old_logo_name and old_logo_name != new_logo_name:
            self.company_logo.storage.delete(old_logo_name)

        clear_app_settings_cache()
        return result

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1, defaults={"singleton_enforcer": True})[0]

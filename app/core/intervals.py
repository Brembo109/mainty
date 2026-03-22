from django.utils.translation import gettext_lazy as _


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

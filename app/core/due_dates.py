from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone


DUE_STATUS_OK = "ok"
DUE_STATUS_WARNING = "warning"
DUE_STATUS_OVERDUE = "overdue"
DUE_STATUS_INACTIVE = "inactive"
DUE_STATUS_UNKNOWN = "unknown"

DUE_STATUS_LABELS = {
    DUE_STATUS_OK: "OK",
    DUE_STATUS_WARNING: "Faellig bald",
    DUE_STATUS_OVERDUE: "Ueberfaellig",
    DUE_STATUS_INACTIVE: "Inaktiv",
    DUE_STATUS_UNKNOWN: "Unbekannt",
}


@dataclass(frozen=True)
class DueStatusResult:
    code: str
    label: str


def add_interval(base_date: date, interval_value: int, interval_unit: str) -> date:
    if interval_unit == "days":
        return base_date + timedelta(days=interval_value)
    if interval_unit == "weeks":
        return base_date + timedelta(weeks=interval_value)
    if interval_unit == "months":
        return _add_months(base_date, interval_value)
    if interval_unit == "years":
        return _add_years(base_date, interval_value)
    raise ValueError(f"Unsupported interval unit: {interval_unit}")


def calculate_due_status(
    *,
    next_due_date: date | None,
    warning_days: int,
    is_active: bool,
    today: date | None = None,
) -> DueStatusResult:
    if not is_active:
        return DueStatusResult(DUE_STATUS_INACTIVE, DUE_STATUS_LABELS[DUE_STATUS_INACTIVE])

    if next_due_date is None:
        return DueStatusResult(DUE_STATUS_UNKNOWN, DUE_STATUS_LABELS[DUE_STATUS_UNKNOWN])

    reference_date = today or timezone.localdate()
    if next_due_date < reference_date:
        return DueStatusResult(DUE_STATUS_OVERDUE, DUE_STATUS_LABELS[DUE_STATUS_OVERDUE])
    if next_due_date <= reference_date + timedelta(days=warning_days):
        return DueStatusResult(DUE_STATUS_WARNING, DUE_STATUS_LABELS[DUE_STATUS_WARNING])
    return DueStatusResult(DUE_STATUS_OK, DUE_STATUS_LABELS[DUE_STATUS_OK])


def _add_months(base_date: date, months: int) -> date:
    zero_based_month = base_date.month - 1 + months
    year = base_date.year + zero_based_month // 12
    month = zero_based_month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _add_years(base_date: date, years: int) -> date:
    year = base_date.year + years
    day = min(base_date.day, monthrange(year, base_date.month)[1])
    return date(year, base_date.month, day)

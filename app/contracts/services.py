from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


CONTRACT_STATUS_ACTIVE = "active"
CONTRACT_STATUS_WARNING = "warning"
CONTRACT_STATUS_EXPIRED = "expired"
CONTRACT_STATUS_NONE = "none"

CONTRACT_STATUS_LABELS = {
    CONTRACT_STATUS_ACTIVE: _("Aktiv"),
    CONTRACT_STATUS_WARNING: _("Läuft bald aus"),
    CONTRACT_STATUS_EXPIRED: _("Abgelaufen"),
    CONTRACT_STATUS_NONE: _("Kein Vertrag"),
}


@dataclass(frozen=True)
class ContractStatusResult:
    code: str
    label: str


def add_months(base_date: date, months: int) -> date:
    zero_based_month = base_date.month - 1 + months
    year = base_date.year + zero_based_month // 12
    month = zero_based_month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_contract_status(
    *,
    end_date: date | None,
    warning_months: int,
    today: date | None = None,
) -> ContractStatusResult:
    if end_date is None:
        return ContractStatusResult(CONTRACT_STATUS_NONE, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_NONE])

    reference_date = today or timezone.localdate()
    if end_date < reference_date:
        return ContractStatusResult(CONTRACT_STATUS_EXPIRED, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_EXPIRED])

    warning_start = add_months(end_date, -warning_months)
    if reference_date >= warning_start:
        return ContractStatusResult(CONTRACT_STATUS_WARNING, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_WARNING])
    return ContractStatusResult(CONTRACT_STATUS_ACTIVE, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_ACTIVE])


def get_contract_remaining_runtime_display(*, end_date: date | None, today: date | None = None) -> str:
    if end_date is None:
        return str(_("Kein Enddatum hinterlegt"))

    reference_date = today or timezone.localdate()
    day_delta = (end_date - reference_date).days
    if day_delta < 0:
        return str(_("seit %(days)s Tagen abgelaufen")) % {"days": abs(day_delta)}
    if day_delta <= 60:
        return str(_("läuft in %(days)s Tagen aus")) % {"days": day_delta}

    months_remaining = _whole_months_between(reference_date, end_date)
    if months_remaining >= 1:
        if months_remaining == 1:
            return str(_("läuft noch %(months)s Monat")) % {"months": months_remaining}
        return str(_("läuft noch %(months)s Monate")) % {"months": months_remaining}
    return str(_("läuft in %(days)s Tagen aus")) % {"days": day_delta}


def summarize_asset_contract_status(asset, *, today: date | None = None) -> ContractStatusResult:
    reference_date = today or timezone.localdate()
    contracts = _get_asset_contracts(asset)
    if not contracts:
        return ContractStatusResult(CONTRACT_STATUS_NONE, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_NONE])

    status_codes = {
        calculate_contract_status(
            end_date=contract.end_date,
            warning_months=contract.warning_months,
            today=reference_date,
        ).code
        for contract in contracts
    }
    if CONTRACT_STATUS_ACTIVE in status_codes:
        return ContractStatusResult(CONTRACT_STATUS_ACTIVE, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_ACTIVE])
    if CONTRACT_STATUS_WARNING in status_codes:
        return ContractStatusResult(CONTRACT_STATUS_WARNING, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_WARNING])
    if CONTRACT_STATUS_EXPIRED in status_codes:
        return ContractStatusResult(CONTRACT_STATUS_EXPIRED, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_EXPIRED])
    return ContractStatusResult(CONTRACT_STATUS_NONE, CONTRACT_STATUS_LABELS[CONTRACT_STATUS_NONE])


def _get_asset_contracts(asset):
    prefetched_contracts = getattr(asset, "_prefetched_objects_cache", {}).get("contracts")
    if prefetched_contracts is not None:
        return prefetched_contracts
    return list(asset.contracts.all())


def _whole_months_between(start_date: date, end_date: date) -> int:
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        months -= 1
    return max(months, 0)


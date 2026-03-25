from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from assets.models import Asset
from contracts.models import MaintenanceContract
from contracts.services import CONTRACT_STATUS_ACTIVE, CONTRACT_STATUS_EXPIRED, CONTRACT_STATUS_WARNING
from core.due_dates import DUE_STATUS_OVERDUE, DUE_STATUS_WARNING
from maintenance.models import MaintenancePlan
from qualification.models import QualificationPlan
from reminders.services import get_dashboard_due_sections
from tasks.models import Task


DEFAULT_SECTION_LIMIT = 10


@dataclass(frozen=True)
class DashboardItem:
    category: str
    category_label: str
    title: str
    asset_label: str
    due_date: date | None
    status_code: str
    status_label: str
    detail_url: str
    updated_at: object | None = None
    priority_label: str = ""
    responsible_label: str = ""


@dataclass(frozen=True)
class RecentDashboardItem:
    category_label: str
    title: str
    asset_label: str
    updated_at: object
    detail_url: str


def build_dashboard_context(*, today: date | None = None, section_limit: int = DEFAULT_SECTION_LIMIT) -> dict:
    reference_date = today or timezone.localdate()
    task_warning_days = settings.TASK_DASHBOARD_WARNING_DAYS

    due_sections = get_dashboard_due_sections(today=reference_date)
    maintenance_items = due_sections["maintenance_all"]
    qualification_items = due_sections["qualification_all"]
    open_task_items, overdue_task_items, upcoming_task_items = _build_task_groups(
        today=reference_date,
        task_warning_days=task_warning_days,
    )
    contract_items = _build_contract_items(today=reference_date)
    expired_contracts = [item for item in contract_items if item.status_code == CONTRACT_STATUS_EXPIRED][:section_limit]
    expiring_contracts = [item for item in contract_items if item.status_code == CONTRACT_STATUS_WARNING][:section_limit]

    overdue_items = sorted(
        [
            *[item for item in maintenance_items if item.status_code == DUE_STATUS_OVERDUE],
            *[item for item in qualification_items if item.status_code == DUE_STATUS_OVERDUE],
            *overdue_task_items,
            *expired_contracts,
        ],
        key=lambda item: (item.due_date is None, item.due_date, item.title.lower()),
    )[:section_limit]
    upcoming_items = sorted(
        [
            *[item for item in maintenance_items if item.status_code == DUE_STATUS_WARNING],
            *[item for item in qualification_items if item.status_code == DUE_STATUS_WARNING],
            *upcoming_task_items,
            *expiring_contracts,
        ],
        key=lambda item: (item.due_date is None, item.due_date, item.title.lower()),
    )[:section_limit]
    recent_items = _build_recent_items(
        maintenance_items=maintenance_items,
        qualification_items=qualification_items,
        open_task_items=open_task_items,
        section_limit=section_limit,
    )

    metrics = {
        "active_assets": Asset.objects.filter(status=Asset.STATUS_ACTIVE).count(),
        "maintenance_plans": MaintenancePlan.objects.count(),
        "qualification_plans": QualificationPlan.objects.count(),
        "open_tasks": len(open_task_items),
        "active_contracts": sum(1 for item in contract_items if item.status_code == CONTRACT_STATUS_ACTIVE),
        "expiring_contracts": len(expiring_contracts),
        "expired_contracts": len(expired_contracts),
        "overdue_tasks": len(overdue_task_items),
        "overdue_maintenance_plans": sum(
            1 for item in maintenance_items if item.status_code == DUE_STATUS_OVERDUE
        ),
        "overdue_qualification_plans": sum(
            1 for item in qualification_items if item.status_code == DUE_STATUS_OVERDUE
        ),
    }

    metric_cards = [
        {
            "title": _("Aktive Assets"),
            "value": metrics["active_assets"],
            "url": reverse("assets:list"),
            "accent": "primary",
        },
        {
            "title": _("Wartungspläne"),
            "value": metrics["maintenance_plans"],
            "url": reverse("maintenance:plan-list"),
            "accent": "info",
        },
        {
            "title": _("Qualifizierungspläne"),
            "value": metrics["qualification_plans"],
            "url": reverse("qualification:plan-list"),
            "accent": "info",
        },
        {
            "title": _("Offene Maßnahmen"),
            "value": metrics["open_tasks"],
            "url": reverse("tasks:list"),
            "accent": "primary",
        },
        {
            "title": _("Aktive Verträge"),
            "value": metrics["active_contracts"],
            "url": reverse("contracts:list") + "?status=active",
            "accent": "success",
        },
        {
            "title": _("Bald endende Verträge"),
            "value": metrics["expiring_contracts"],
            "url": reverse("contracts:list") + "?status=warning",
            "accent": "warning",
        },
        {
            "title": _("Abgelaufene Verträge"),
            "value": metrics["expired_contracts"],
            "url": reverse("contracts:list") + "?status=expired",
            "accent": "danger",
        },
        {
            "title": _("Überfällige Maßnahmen"),
            "value": metrics["overdue_tasks"],
            "url": reverse("tasks:list") + "?overdue=yes",
            "accent": "danger",
        },
        {
            "title": _("Überfällige Wartungspläne"),
            "value": metrics["overdue_maintenance_plans"],
            "url": reverse("maintenance:plan-list") + "?due_status=overdue",
            "accent": "danger",
        },
        {
            "title": _("Überfällige Qualifizierungspläne"),
            "value": metrics["overdue_qualification_plans"],
            "url": reverse("qualification:plan-list") + "?due_status=overdue",
            "accent": "danger",
        },
    ]

    return {
        "reference_date": reference_date,
        "metrics": metrics,
        "metric_cards": metric_cards,
        "overdue_items": overdue_items,
        "upcoming_items": upcoming_items,
        "open_tasks": open_task_items[:section_limit],
        "expiring_contracts": expiring_contracts,
        "expired_contracts": expired_contracts,
        "recent_items": recent_items,
        "task_warning_days": task_warning_days,
        "due_soon_maintenance_items": due_sections["maintenance_due_soon"][:5],
        "overdue_maintenance_items": due_sections["maintenance_overdue"][:5],
        "due_soon_qualification_items": due_sections["qualification_due_soon"][:5],
        "overdue_qualification_items": due_sections["qualification_overdue"][:5],
    }


def _build_task_groups(*, today: date, task_warning_days: int):
    open_tasks = list(
        Task.objects.exclude(status=Task.STATUS_DONE)
        .select_related("asset", "responsible_user")
        .only(
            "pk",
            "title",
            "due_date",
            "priority",
            "status",
            "updated_at",
            "asset__id",
            "asset__asset_id",
            "asset__name",
            "responsible_user__username",
        )
        .order_by("due_date", "title")
    )

    open_items = []
    overdue_items = []
    upcoming_items = []
    warning_threshold = today + timedelta(days=task_warning_days)

    for task in open_tasks:
        item = DashboardItem(
            category="task",
            category_label=_("Maßnahme"),
            title=task.title,
            asset_label=_format_asset_label(task.asset),
            due_date=task.due_date,
            status_code="overdue" if task.is_overdue else task.status,
            status_label=_task_status_label(task),
            detail_url=reverse("tasks:detail", kwargs={"pk": task.pk}),
            updated_at=task.updated_at,
            priority_label=task.get_priority_display(),
            responsible_label=task.responsible_user.username if task.responsible_user else "-",
        )
        open_items.append(item)
        if task.is_overdue:
            overdue_items.append(item)
        elif task.due_date and task.due_date <= warning_threshold:
            upcoming_items.append(
                DashboardItem(
                    category=item.category,
                    category_label=item.category_label,
                    title=item.title,
                    asset_label=item.asset_label,
                    due_date=item.due_date,
                    status_code=DUE_STATUS_WARNING,
                    status_label=_("Fällig bald"),
                    detail_url=item.detail_url,
                    updated_at=item.updated_at,
                    priority_label=item.priority_label,
                    responsible_label=item.responsible_label,
                )
            )

    return open_items, overdue_items, upcoming_items


def _build_contract_items(*, today: date):
    contracts = list(MaintenanceContract.objects.prefetch_related("assets").order_by("end_date", "title"))
    items = []
    for contract in contracts:
        asset_labels = [asset.asset_id for asset in contract.assets.all()]
        items.append(
            DashboardItem(
                category="contract",
                category_label=_("Vertrag"),
                title=contract.title,
                asset_label=", ".join(asset_labels) if asset_labels else "-",
                due_date=contract.end_date,
                status_code=contract.status.code,
                status_label=contract.status.label,
                detail_url=reverse("contracts:detail", kwargs={"pk": contract.pk}),
                updated_at=contract.updated_at,
            )
        )
    return items


def _build_recent_items(*, maintenance_items, qualification_items, open_task_items, section_limit: int):
    recent_items = [
        *[
            RecentDashboardItem(
                category_label=item.category_label,
                title=item.title,
                asset_label=item.asset_label,
                updated_at=item.updated_at,
                detail_url=item.detail_url,
            )
            for item in maintenance_items
        ],
        *[
            RecentDashboardItem(
                category_label=item.category_label,
                title=item.title,
                asset_label=item.asset_label,
                updated_at=item.updated_at,
                detail_url=item.detail_url,
            )
            for item in qualification_items
        ],
        *[
            RecentDashboardItem(
                category_label=item.category_label,
                title=item.title,
                asset_label=item.asset_label,
                updated_at=item.updated_at,
                detail_url=item.detail_url,
            )
            for item in open_task_items
        ],
        *[
            RecentDashboardItem(
                category_label=_("Asset"),
                title=asset.name,
                asset_label=asset.asset_id,
                updated_at=asset.updated_at,
                detail_url=reverse("assets:detail", kwargs={"pk": asset.pk}),
            )
            for asset in Asset.objects.only("id", "asset_id", "name", "updated_at").order_by("-updated_at")[
                :section_limit
            ]
        ],
    ]
    return sorted(recent_items, key=lambda item: item.updated_at, reverse=True)[:section_limit]


def _format_asset_label(asset):
    if asset is None:
        return "-"
    return f"{asset.asset_id} - {asset.name}"


def _task_status_label(task: Task) -> str:
    if task.is_overdue:
        return str(_("Überfällig"))
    return task.get_status_display()

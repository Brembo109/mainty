from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage
from django.db.models import OuterRef, Q, Subquery
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.roles import ROLE_ADMIN, ROLE_USER
from core.due_dates import DUE_STATUS_OVERDUE, DUE_STATUS_WARNING, add_interval, calculate_due_status
from core.models import SystemSettings
from core.runtime import get_app_settings
from maintenance.models import MaintenanceEvent, MaintenancePlan
from qualification.models import QualificationEvent, QualificationPlan

from .models import NotificationLog

User = get_user_model()


@dataclass(frozen=True)
class ReminderRecipient:
    user: object | None
    email: str
    display_name: str


@dataclass(frozen=True)
class DueReminderItem:
    category: str
    category_label: str
    title: str
    asset_label: str
    due_date: date | None
    status_code: str
    status_label: str
    detail_url: str
    responsible_person: str
    object_id: int
    content_type_id: int
    updated_at: object | None = None

    def days_until_due(self, today: date | None = None) -> int | None:
        if self.due_date is None:
            return None
        reference_date = today or timezone.localdate()
        return (self.due_date - reference_date).days

    def days_overdue(self, today: date | None = None) -> int:
        days_until_due = self.days_until_due(today=today)
        if days_until_due is None or days_until_due >= 0:
            return 0
        return abs(days_until_due)


def get_dashboard_due_sections(*, today: date | None = None) -> dict[str, list[DueReminderItem]]:
    reference_date = today or timezone.localdate()
    settings_obj = SystemSettings.load()
    maintenance_all = _build_due_items(
        plan_model=MaintenancePlan,
        event_model=MaintenanceEvent,
        category="maintenance",
        category_label=_("Wartung"),
        detail_url_name="maintenance:plan-detail",
        upcoming_days=settings_obj.maintenance_upcoming_days,
        today=reference_date,
    )
    qualification_all = _build_due_items(
        plan_model=QualificationPlan,
        event_model=QualificationEvent,
        category="qualification",
        category_label=_("Qualifizierung"),
        detail_url_name="qualification:plan-detail",
        upcoming_days=settings_obj.qualification_upcoming_days,
        today=reference_date,
    )
    return {
        "maintenance_all": maintenance_all,
        "maintenance_due_soon": [item for item in maintenance_all if item.status_code == DUE_STATUS_WARNING],
        "maintenance_overdue": [item for item in maintenance_all if item.status_code == DUE_STATUS_OVERDUE],
        "qualification_all": qualification_all,
        "qualification_due_soon": [item for item in qualification_all if item.status_code == DUE_STATUS_WARNING],
        "qualification_overdue": [item for item in qualification_all if item.status_code == DUE_STATUS_OVERDUE],
    }


def get_due_reminder_items(*, today: date | None = None) -> dict[str, list[DueReminderItem]]:
    sections = get_dashboard_due_sections(today=today)
    return {
        "upcoming": sorted(
            [*sections["maintenance_due_soon"], *sections["qualification_due_soon"]],
            key=lambda item: (item.due_date is None, item.due_date, item.title.lower()),
        ),
        "overdue": sorted(
            [*sections["maintenance_overdue"], *sections["qualification_overdue"]],
            key=lambda item: (item.due_date is None, item.due_date, item.title.lower()),
        ),
    }


def resolve_recipients_for_item(item: DueReminderItem) -> list[ReminderRecipient]:
    recipients = []
    if item.responsible_person:
        recipients.extend(_match_responsible_users(item.responsible_person))
    if not recipients:
        recipients.extend(_users_for_role(ROLE_USER))
    if not recipients:
        recipients.extend(_users_for_role(ROLE_ADMIN))
    return _deduplicate_recipients(recipients)


def send_due_notifications(*, dry_run: bool = False, today: date | None = None) -> dict[str, int]:
    reference_date = today or timezone.localdate()
    settings_obj = SystemSettings.load()
    counters = {"upcoming": 0, "overdue": 0, "skipped": 0, "failed": 0}

    if not settings_obj.notifications_enabled:
        return counters

    reminder_items = get_due_reminder_items(today=reference_date)

    if settings_obj.send_upcoming_reminders:
        for item in reminder_items["upcoming"]:
            for recipient in resolve_recipients_for_item(item):
                if not should_send_item_notification(
                    notification_type=NotificationLog.TYPE_UPCOMING,
                    item=item,
                    recipient_email=recipient.email,
                    only_notify_once_per_status=settings_obj.only_notify_once_per_status,
                    today=reference_date,
                ):
                    counters["skipped"] += 1
                    continue
                if _send_due_email(
                    item=item,
                    recipient=recipient,
                    notification_type=NotificationLog.TYPE_UPCOMING,
                    dry_run=dry_run,
                    today=reference_date,
                ):
                    counters["upcoming"] += 1
                else:
                    counters["failed"] += 1

    if settings_obj.send_overdue_reminders:
        for item in reminder_items["overdue"]:
            if item.days_overdue(today=reference_date) < settings_obj.overdue_escalation_days:
                counters["skipped"] += 1
                continue
            for recipient in resolve_recipients_for_item(item):
                if not should_send_item_notification(
                    notification_type=NotificationLog.TYPE_OVERDUE,
                    item=item,
                    recipient_email=recipient.email,
                    only_notify_once_per_status=settings_obj.only_notify_once_per_status,
                    today=reference_date,
                ):
                    counters["skipped"] += 1
                    continue
                if _send_due_email(
                    item=item,
                    recipient=recipient,
                    notification_type=NotificationLog.TYPE_OVERDUE,
                    dry_run=dry_run,
                    today=reference_date,
                ):
                    counters["overdue"] += 1
                else:
                    counters["failed"] += 1
    return counters


def send_digest_notifications(*, frequency: str, dry_run: bool = False, today: date | None = None) -> dict[str, int]:
    reference_date = today or timezone.localdate()
    settings_obj = SystemSettings.load()
    counters = {"sent": 0, "skipped": 0, "failed": 0}

    if not settings_obj.notifications_enabled:
        return counters
    if frequency == "daily" and not settings_obj.send_daily_digest:
        return counters
    if frequency == "weekly" and not settings_obj.send_weekly_digest:
        return counters

    notification_type = (
        NotificationLog.TYPE_DIGEST_DAILY if frequency == "daily" else NotificationLog.TYPE_DIGEST_WEEKLY
    )
    iso_calendar = reference_date.isocalendar()
    period_key = reference_date.isoformat() if frequency == "daily" else f"{iso_calendar.year}-W{iso_calendar.week:02d}"
    reminder_items = get_due_reminder_items(today=reference_date)
    recipients_map: dict[str, dict[str, object]] = {}

    for group_name in ("upcoming", "overdue"):
        for item in reminder_items[group_name]:
            if group_name == "overdue" and item.days_overdue(today=reference_date) < settings_obj.overdue_escalation_days:
                continue
            for recipient in resolve_recipients_for_item(item):
                bucket = recipients_map.setdefault(
                    recipient.email.lower(),
                    {"recipient": recipient, "upcoming": [], "overdue": []},
                )
                bucket[group_name].append(item)

    for bucket in recipients_map.values():
        recipient = bucket["recipient"]
        if not bucket["upcoming"] and not bucket["overdue"]:
            counters["skipped"] += 1
            continue
        if NotificationLog.objects.filter(
            notification_type=notification_type,
            recipient_email__iexact=recipient.email,
            period_key=period_key,
            status=NotificationLog.STATUS_SUCCESS,
        ).exists():
            counters["skipped"] += 1
            continue
        if _send_digest_email(
            recipient=recipient,
            upcoming_items=bucket["upcoming"],
            overdue_items=bucket["overdue"],
            notification_type=notification_type,
            period_key=period_key,
            dry_run=dry_run,
            today=reference_date,
        ):
            counters["sent"] += 1
        else:
            counters["failed"] += 1
    return counters


def should_send_item_notification(
    *,
    notification_type: str,
    item: DueReminderItem,
    recipient_email: str,
    only_notify_once_per_status: bool,
    today: date | None = None,
) -> bool:
    reference_date = today or timezone.localdate()
    queryset = NotificationLog.objects.filter(
        notification_type=notification_type,
        content_type_id=item.content_type_id,
        object_id=str(item.object_id),
        recipient_email__iexact=recipient_email,
        status=NotificationLog.STATUS_SUCCESS,
    )
    if only_notify_once_per_status:
        return not queryset.exists()
    return not queryset.filter(sent_at__date=reference_date).exists()


def _build_due_items(*, plan_model, event_model, category: str, category_label, detail_url_name: str, upcoming_days: int, today: date) -> list[DueReminderItem]:
    latest_event_subquery = Subquery(
        event_model.objects.filter(plan_id=OuterRef("pk")).order_by("-performed_on", "-pk").values("performed_on")[:1]
    )
    queryset = (
        plan_model.objects.select_related("asset")
        .annotate(latest_event_date=latest_event_subquery)
        .only(
            "pk",
            "title",
            "interval_value",
            "interval_unit",
            "responsible_person",
            "is_active",
            "updated_at",
            "asset__asset_id",
            "asset__name",
            "asset__commissioning_date",
        )
    )
    content_type_id = ContentType.objects.get_for_model(plan_model).pk
    items = []
    for plan in queryset:
        if not plan.is_active:
            continue
        base_date = plan.latest_event_date or plan.asset.commissioning_date
        next_due_date = add_interval(base_date, plan.interval_value, plan.interval_unit) if base_date else None
        due_status = calculate_due_status(
            next_due_date=next_due_date,
            warning_days=upcoming_days,
            is_active=plan.is_active,
            today=today,
        )
        if due_status.code not in {DUE_STATUS_WARNING, DUE_STATUS_OVERDUE}:
            continue
        items.append(
            DueReminderItem(
                category=category,
                category_label=str(category_label),
                title=plan.title,
                asset_label=f"{plan.asset.asset_id} - {plan.asset.name}",
                due_date=next_due_date,
                status_code=due_status.code,
                status_label=str(due_status.label),
                detail_url=reverse(detail_url_name, kwargs={"pk": plan.pk}),
                responsible_person=plan.responsible_person,
                object_id=plan.pk,
                content_type_id=content_type_id,
                updated_at=plan.updated_at,
            )
        )
    return sorted(items, key=lambda item: (item.due_date is None, item.due_date, item.title.lower()))


def _send_due_email(
    *,
    item: DueReminderItem,
    recipient: ReminderRecipient,
    notification_type: str,
    dry_run: bool,
    today: date,
) -> bool:
    subject = _build_due_subject(item=item, notification_type=notification_type)
    body = _build_due_body(item=item, recipient=recipient, notification_type=notification_type, today=today)
    return _send_email(
        subject=subject,
        body=body,
        recipient=recipient,
        notification_type=notification_type,
        item=item,
        dry_run=dry_run,
    )


def _send_digest_email(
    *,
    recipient: ReminderRecipient,
    upcoming_items: list[DueReminderItem],
    overdue_items: list[DueReminderItem],
    notification_type: str,
    period_key: str,
    dry_run: bool,
    today: date,
) -> bool:
    frequency_label = (
        str(_("Tägliche Zusammenfassung"))
        if notification_type == NotificationLog.TYPE_DIGEST_DAILY
        else str(_("Wöchentliche Zusammenfassung"))
    )
    subject = str(_("%(label)s Mainty")) % {"label": frequency_label}
    body = _build_digest_body(
        recipient=recipient,
        upcoming_items=upcoming_items,
        overdue_items=overdue_items,
        frequency_label=frequency_label,
        today=today,
    )
    return _send_email(
        subject=subject,
        body=body,
        recipient=recipient,
        notification_type=notification_type,
        period_key=period_key,
        dry_run=dry_run,
    )


def _send_email(
    *,
    subject: str,
    body: str,
    recipient: ReminderRecipient,
    notification_type: str,
    dry_run: bool,
    item: DueReminderItem | None = None,
    period_key: str = "",
) -> bool:
    from_email = SystemSettings.load().notification_from_email or settings.DEFAULT_FROM_EMAIL
    if dry_run:
        return True
    try:
        EmailMessage(subject=subject, body=body, from_email=from_email, to=[recipient.email]).send(fail_silently=False)
        NotificationLog.objects.create(
            notification_type=notification_type,
            content_type_id=item.content_type_id if item else None,
            object_id=str(item.object_id) if item else "",
            recipient_user=recipient.user,
            recipient_email=recipient.email,
            subject=subject,
            status=NotificationLog.STATUS_SUCCESS,
            period_key=period_key,
        )
        return True
    except Exception as exc:
        NotificationLog.objects.create(
            notification_type=notification_type,
            content_type_id=item.content_type_id if item else None,
            object_id=str(item.object_id) if item else "",
            recipient_user=recipient.user,
            recipient_email=recipient.email,
            subject=subject,
            status=NotificationLog.STATUS_FAILED,
            period_key=period_key,
            error_message=str(exc),
        )
        return False


def _build_due_subject(*, item: DueReminderItem, notification_type: str) -> str:
    if notification_type == NotificationLog.TYPE_OVERDUE:
        return str(_("Überfällig: %(type)s %(title)s")) % {"type": item.category_label, "title": item.title}
    return str(_("Fällig bald: %(type)s %(title)s")) % {"type": item.category_label, "title": item.title}


def _build_due_body(*, item: DueReminderItem, recipient: ReminderRecipient, notification_type: str, today: date) -> str:
    lines = [
        str(_("Hallo %(name)s,")) % {"name": recipient.display_name or recipient.email},
        "",
    ]
    if notification_type == NotificationLog.TYPE_OVERDUE:
        lines.append(
            str(_("der folgende Eintrag in Mainty ist seit %(days)s Tagen überfällig:"))
            % {"days": item.days_overdue(today=today)}
        )
    else:
        lines.append(
            str(_("der folgende Eintrag in Mainty wird in %(days)s Tagen fällig:"))
            % {"days": max(item.days_until_due(today=today) or 0, 0)}
        )
    lines.extend(
        [
            "",
            str(_("Typ: %(value)s")) % {"value": item.category_label},
            str(_("Titel: %(value)s")) % {"value": item.title},
            str(_("Asset: %(value)s")) % {"value": item.asset_label},
            str(_("Fällig am: %(value)s")) % {"value": item.due_date.strftime("%d.%m.%Y") if item.due_date else "-"},
            str(_("Verantwortlich: %(value)s")) % {"value": item.responsible_person or "-"},
            str(_("Status: %(value)s")) % {"value": item.status_label},
        ]
    )
    absolute_url = _absolute_url(item.detail_url)
    if absolute_url:
        lines.extend(["", str(_("Direktlink: %(value)s")) % {"value": absolute_url}])
    lines.extend(["", str(_("Bitte prüfe den Eintrag in Mainty und plane die nächsten Schritte ein."))])
    return "\n".join(lines)


def _build_digest_body(
    *,
    recipient: ReminderRecipient,
    upcoming_items: list[DueReminderItem],
    overdue_items: list[DueReminderItem],
    frequency_label: str,
    today: date,
) -> str:
    lines = [
        str(_("Hallo %(name)s,")) % {"name": recipient.display_name or recipient.email},
        "",
        str(_("%(label)s der fälligen und überfälligen Einträge in Mainty:")) % {"label": frequency_label},
        "",
    ]
    lines.extend(_render_digest_group(_("Überfällige Einträge"), overdue_items, overdue=True, today=today))
    lines.append("")
    lines.extend(_render_digest_group(_("Bald fällige Einträge"), upcoming_items, overdue=False, today=today))
    return "\n".join(lines)


def _render_digest_group(title, items: list[DueReminderItem], *, overdue: bool, today: date) -> list[str]:
    lines = [str(title)]
    if not items:
        lines.append(str(_("Keine Einträge.")))
        return lines
    for item in items:
        timing = (
            str(_("%(days)s Tage überfällig")) % {"days": item.days_overdue(today=today)}
            if overdue
            else str(_("fällig in %(days)s Tagen")) % {"days": max(item.days_until_due(today=today) or 0, 0)}
        )
        absolute_url = _absolute_url(item.detail_url)
        lines.append(
            str(_("- %(type)s | %(title)s | %(asset)s | %(due)s | %(timing)s"))
            % {
                "type": item.category_label,
                "title": item.title,
                "asset": item.asset_label,
                "due": item.due_date.strftime("%d.%m.%Y") if item.due_date else "-",
                "timing": timing,
            }
        )
        if absolute_url:
            lines.append(str(_("  Link: %(value)s")) % {"value": absolute_url})
    return lines


def _absolute_url(path: str) -> str:
    base_url = get_app_settings().app_public_url.rstrip("/")
    if not base_url:
        return ""
    return f"{base_url}{path}"


def _users_for_role(role_name: str) -> list[ReminderRecipient]:
    return [
        ReminderRecipient(user=user, email=user.email.strip(), display_name=user.get_full_name().strip() or user.username)
        for user in User.objects.filter(groups__name=role_name, is_active=True).exclude(email="").distinct()
    ]


def _match_responsible_users(responsible_person: str) -> list[ReminderRecipient]:
    candidate = responsible_person.strip()
    if not candidate:
        return []
    full_name_query = Q(first_name__iexact=candidate) | Q(last_name__iexact=candidate)
    if " " in candidate:
        first_name, last_name = candidate.split(" ", 1)
        full_name_query |= Q(first_name__iexact=first_name.strip(), last_name__iexact=last_name.strip())
    queryset = (
        User.objects.filter(is_active=True)
        .exclude(email="")
        .filter(
            Q(username__iexact=candidate)
            | Q(email__iexact=candidate)
            | Q(profile__user_code__iexact=candidate)
            | full_name_query
        )
        .distinct()
    )
    return [
        ReminderRecipient(user=user, email=user.email.strip(), display_name=user.get_full_name().strip() or user.username)
        for user in queryset
    ]


def _deduplicate_recipients(recipients: list[ReminderRecipient]) -> list[ReminderRecipient]:
    seen = set()
    unique = []
    for recipient in recipients:
        key = recipient.email.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(recipient)
    return unique

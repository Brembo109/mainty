from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset
from core.models import SystemSettings
from maintenance.models import MaintenancePlan
from qualification.models import QualificationPlan

from .models import NotificationLog
from .services import get_due_reminder_items, resolve_recipients_for_item


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="mainty@example.com")
class ReminderTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.editor_group, _ = Group.objects.get_or_create(name=ROLE_EDITOR)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(
            username="admin",
            password="pass-12345",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
        )
        self.editor_user = user_model.objects.create_user(
            username="editor",
            password="pass-12345",
            email="editor@example.com",
            first_name="Eva",
            last_name="Editor",
        )
        self.viewer_user = user_model.objects.create_user(
            username="viewer",
            password="pass-12345",
            email="",
        )
        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)
        self.editor_user.profile.user_code = "EE"
        self.editor_user.profile.save()

        self.asset = Asset.objects.create(
            asset_id="A-100",
            name="Mischer",
            commissioning_date=timezone.localdate() - timedelta(days=30),
            status=Asset.STATUS_ACTIVE,
        )
        self.maintenance_plan = MaintenancePlan.objects.create(
            asset=self.asset,
            title="Wartung bald fällig",
            interval_value=35,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=3,
            responsible_person="editor",
            is_active=True,
        )
        self.qualification_plan = QualificationPlan.objects.create(
            asset=self.asset,
            title="Qualifizierung überfällig",
            interval_value=10,
            interval_unit=QualificationPlan.INTERVAL_DAYS,
            warning_days=3,
            responsible_person="EE",
            is_active=True,
        )
        settings_obj = SystemSettings.load()
        settings_obj.notifications_enabled = True
        settings_obj.notification_from_email = "noreply@mainty.example.com"
        settings_obj.send_upcoming_reminders = True
        settings_obj.send_overdue_reminders = True
        settings_obj.send_daily_digest = True
        settings_obj.send_weekly_digest = True
        settings_obj.maintenance_upcoming_days = 7
        settings_obj.qualification_upcoming_days = 14
        settings_obj.overdue_escalation_days = 0
        settings_obj.only_notify_once_per_status = False
        settings_obj.app_public_url = "https://mainty.example.com"
        settings_obj.save()

    def test_due_item_selection_returns_upcoming_and_overdue_items(self):
        items = get_due_reminder_items()

        self.assertEqual(len(items["upcoming"]), 1)
        self.assertEqual(len(items["overdue"]), 1)
        self.assertEqual(items["upcoming"][0].title, "Wartung bald fällig")
        self.assertEqual(items["overdue"][0].title, "Qualifizierung überfällig")

    def test_recipient_resolution_prefers_responsible_person_matches(self):
        item = get_due_reminder_items()["upcoming"][0]
        recipients = resolve_recipients_for_item(item)

        self.assertEqual([recipient.email for recipient in recipients], ["editor@example.com"])

    def test_send_due_reminders_command_sends_emails_and_logs_them(self):
        out = StringIO()
        call_command("send_due_reminders", stdout=out)

        self.assertIn("Due reminders:", out.getvalue())
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(NotificationLog.objects.filter(status=NotificationLog.STATUS_SUCCESS).count(), 2)
        self.assertIn("https://mainty.example.com/maintenance/plans/", mail.outbox[0].body)

    def test_send_daily_digest_sends_one_mail_per_recipient(self):
        out = StringIO()
        call_command("send_digest_notifications", "--frequency", "daily", stdout=out)

        self.assertIn("Digest daily:", out.getvalue())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(NotificationLog.objects.filter(notification_type=NotificationLog.TYPE_DIGEST_DAILY).count(), 1)
        self.assertIn("Überfällige Einträge", mail.outbox[0].body)

    def test_due_reminders_are_not_resent_on_same_day(self):
        call_command("send_due_reminders")
        first_mail_count = len(mail.outbox)

        call_command("send_due_reminders")

        self.assertEqual(len(mail.outbox), first_mail_count)

import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from accounts.permissions import assign_default_role_permissions
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset
from audit.models import AuditLog
from core.models import SystemSettings
from core.runtime import apply_runtime_settings, clear_app_settings_cache, get_app_settings
from maintenance.models import MaintenancePlan
from qualification.models import QualificationPlan
from tasks.models import Task


class CoreViewsTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.today = timezone.localdate()
        self.user_model = get_user_model()
        assign_default_role_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.editor_group, _ = Group.objects.get_or_create(name=ROLE_EDITOR)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)

        self.admin_user = self.user_model.objects.create_user("admin_user", password="pass-12345")
        self.editor_user = self.user_model.objects.create_user("editor_user", password="pass-12345")
        self.viewer_user = self.user_model.objects.create_user("viewer_user", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.active_asset = Asset.objects.create(
            asset_id="A-100",
            name="Mischer",
            commissioning_date=self.today - timedelta(days=30),
            status=Asset.STATUS_ACTIVE,
        )
        self.inactive_asset = Asset.objects.create(
            asset_id="A-200",
            name="Reservepumpe",
            commissioning_date=self.today - timedelta(days=15),
            status=Asset.STATUS_INACTIVE,
        )

        self.overdue_maintenance = MaintenancePlan.objects.create(
            asset=self.active_asset,
            title="Wartung überfällig",
            interval_value=10,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=3,
            is_active=True,
        )
        self.upcoming_maintenance = MaintenancePlan.objects.create(
            asset=self.active_asset,
            title="Wartung bald fällig",
            interval_value=32,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=3,
            is_active=True,
        )
        MaintenancePlan.objects.create(
            asset=self.inactive_asset,
            title="Inaktive Wartung",
            interval_value=5,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=2,
            is_active=False,
        )

        self.overdue_qualification = QualificationPlan.objects.create(
            asset=self.active_asset,
            title="Qualifizierung überfällig",
            interval_value=7,
            interval_unit=QualificationPlan.INTERVAL_DAYS,
            warning_days=2,
            is_active=True,
        )
        self.upcoming_qualification = QualificationPlan.objects.create(
            asset=self.active_asset,
            title="Qualifizierung bald fällig",
            interval_value=31,
            interval_unit=QualificationPlan.INTERVAL_DAYS,
            warning_days=2,
            is_active=True,
        )

        self.overdue_task = Task.objects.create(
            asset=self.active_asset,
            title="Überfällige Maßnahme",
            due_date=self.today - timedelta(days=1),
            priority=Task.PRIORITY_HIGH,
            status=Task.STATUS_OPEN,
            responsible_user=self.editor_user,
        )
        self.upcoming_task = Task.objects.create(
            asset=self.active_asset,
            title="Bald fällige Maßnahme",
            due_date=self.today + timedelta(days=3),
            priority=Task.PRIORITY_MEDIUM,
            status=Task.STATUS_IN_PROGRESS,
            responsible_user=self.admin_user,
        )
        Task.objects.create(
            asset=self.active_asset,
            title="Erledigte Maßnahme",
            due_date=self.today - timedelta(days=2),
            priority=Task.PRIORITY_LOW,
            status=Task.STATUS_DONE,
            responsible_user=self.viewer_user,
        )

    def tearDown(self):
        clear_app_settings_cache()
        shutil.rmtree(self.media_root, ignore_errors=True)
        super().tearDown()

    def _build_test_logo(self, name="company-logo.png"):
        return SimpleUploadedFile(
            name,
            (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
                b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            content_type="image/png",
        )

    def test_homepage_returns_ok(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        login_url = reverse("accounts:login")
        expected_target = f"{login_url}?next={reverse('core:dashboard')}"
        self.assertRedirects(response, expected_target)

    def test_viewer_can_access_dashboard(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_editor_can_access_dashboard(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_dashboard(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_only_admin_can_access_settings_page(self):
        self.client.force_login(self.viewer_user)
        viewer_response = self.client.get(reverse("core:settings"))
        self.assertEqual(viewer_response.status_code, 403)

        self.client.force_login(self.editor_user)
        editor_response = self.client.get(reverse("core:settings"))
        self.assertEqual(editor_response.status_code, 403)

        self.client.force_login(self.admin_user)
        admin_response = self.client.get(reverse("core:settings"))
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "Netzwerk / Zugriff")
        self.assertContains(admin_response, "Benachrichtigungen / Erinnerungen")
        self.assertContains(
            admin_response,
            "Änderungen an diesen Einstellungen erfordern einen Neustart der Anwendung",
        )

    def test_settings_values_are_saved_correctly(self):
        with self.settings(MEDIA_ROOT=self.media_root):
            self.client.force_login(self.admin_user)
            response = self.client.post(
                reverse("core:settings"),
                {
                    "default_maintenance_warning_days": 9,
                    "default_maintenance_interval_value": 45,
                    "default_maintenance_interval_unit": MaintenancePlan.INTERVAL_DAYS,
                    "default_qualification_warning_days": 21,
                    "default_qualification_interval_value": 6,
                    "default_qualification_interval_unit": QualificationPlan.INTERVAL_MONTHS,
                    "notifications_enabled": "on",
                    "notification_from_email": "noreply@example.com",
                    "send_upcoming_reminders": "on",
                    "send_overdue_reminders": "on",
                    "send_daily_digest": "on",
                    "maintenance_upcoming_days": 10,
                    "qualification_upcoming_days": 20,
                    "overdue_escalation_days": 2,
                    "only_notify_once_per_status": "on",
                    "app_public_url": "https://mainty.example.com",
                    "allowed_hosts": "mainty.example.com, localhost, testserver",
                    "csrf_trusted_origins": "https://mainty.example.com, https://proxy.example.net",
                    "force_https": "on",
                },
            )

            self.assertRedirects(response, reverse("core:settings"))
            system_settings = SystemSettings.load()
            self.assertEqual(system_settings.default_maintenance_warning_days, 9)
            self.assertEqual(system_settings.default_maintenance_interval_value, 45)
            self.assertEqual(system_settings.default_qualification_warning_days, 21)
            self.assertEqual(system_settings.default_qualification_interval_value, 6)
            self.assertTrue(system_settings.notifications_enabled)
            self.assertEqual(system_settings.notification_from_email, "noreply@example.com")
            self.assertEqual(system_settings.maintenance_upcoming_days, 10)
            self.assertEqual(system_settings.qualification_upcoming_days, 20)
            self.assertEqual(system_settings.overdue_escalation_days, 2)
            self.assertTrue(system_settings.only_notify_once_per_status)
            self.assertEqual(system_settings.app_public_url, "https://mainty.example.com")
            self.assertEqual(system_settings.allowed_hosts, "mainty.example.com, localhost, testserver")
            self.assertEqual(
                system_settings.csrf_trusted_origins,
                "https://mainty.example.com, https://proxy.example.net",
            )
            self.assertTrue(system_settings.force_https)
            self.assertFalse(system_settings.debug_mode)

            audit_entry = AuditLog.objects.filter(model_name="SystemSettings").latest("id")
            self.assertEqual(audit_entry.user, self.admin_user)

    def test_admin_can_upload_company_logo_in_settings(self):
        with self.settings(MEDIA_ROOT=self.media_root):
            self.client.force_login(self.admin_user)
            response = self.client.post(
                reverse("core:settings"),
                {
                    "default_maintenance_warning_days": 7,
                    "default_maintenance_interval_value": 30,
                    "default_maintenance_interval_unit": MaintenancePlan.INTERVAL_DAYS,
                    "default_qualification_warning_days": 14,
                    "default_qualification_interval_value": 12,
                    "default_qualification_interval_unit": QualificationPlan.INTERVAL_MONTHS,
                    "notifications_enabled": "on",
                    "notification_from_email": "noreply@example.com",
                    "send_upcoming_reminders": "on",
                    "send_overdue_reminders": "on",
                    "send_daily_digest": "on",
                    "send_weekly_digest": "on",
                    "maintenance_upcoming_days": 7,
                    "qualification_upcoming_days": 14,
                    "overdue_escalation_days": 0,
                    "app_public_url": "https://mainty.example.com",
                    "allowed_hosts": "mainty.example.com, localhost, testserver",
                    "csrf_trusted_origins": "https://mainty.example.com",
                    "company_logo": self._build_test_logo(),
                },
            )

            self.assertRedirects(response, reverse("core:settings"))
            settings = SystemSettings.load()
            self.assertTrue(settings.company_logo.name.startswith("branding/"))

    def test_login_page_and_header_show_company_logo_when_configured(self):
        with self.settings(MEDIA_ROOT=self.media_root):
            settings = SystemSettings.load()
            settings.company_logo.save("brand-header.png", self._build_test_logo("brand-header.png"), save=True)

            self.viewer_user.first_name = "Marc"
            self.viewer_user.last_name = "Heyer"
            self.viewer_user.save()
            self.viewer_user.profile.user_code = "MH"
            self.viewer_user.profile.save()

            login_response = self.client.get(reverse("accounts:login"))
            self.assertEqual(login_response.status_code, 200)
            self.assertContains(login_response, settings.company_logo.url)
            self.assertContains(login_response, "img/mainty-logo.svg")
            self.assertContains(login_response, 'action="/i18n/setlang/"')
            self.assertContains(login_response, "data-theme-toggle")

            self.client.force_login(self.viewer_user)
            dashboard_response = self.client.get(reverse("core:dashboard"))
            self.assertContains(dashboard_response, settings.company_logo.url)
            self.assertContains(dashboard_response, "img/mainty-logo.svg")
            self.assertContains(dashboard_response, "Marc Heyer [MH]")
            self.assertContains(dashboard_response, "data-theme-toggle")

    def test_runtime_settings_helper_uses_database_values(self):
        system_settings = SystemSettings.load()
        system_settings.app_public_url = "https://mainty.example.com"
        system_settings.allowed_hosts = "mainty.example.com, localhost"
        system_settings.csrf_trusted_origins = "https://mainty.example.com, https://proxy.example.net"
        system_settings.force_https = True
        system_settings.debug_mode = True
        system_settings.save()

        clear_app_settings_cache()
        runtime_settings = get_app_settings()

        self.assertEqual(runtime_settings.app_public_url, "https://mainty.example.com")
        self.assertEqual(runtime_settings.allowed_hosts, ("mainty.example.com", "localhost"))
        self.assertEqual(
            runtime_settings.csrf_trusted_origins,
            ("https://mainty.example.com", "https://proxy.example.net"),
        )
        self.assertTrue(runtime_settings.force_https)
        self.assertTrue(runtime_settings.debug_mode)

    @override_settings(ALLOWED_HOSTS=["localhost"])
    def test_database_allowed_hosts_are_applied_at_runtime(self):
        system_settings = SystemSettings.load()
        system_settings.allowed_hosts = "mainty.example.com, localhost"
        system_settings.save()

        clear_app_settings_cache()
        apply_runtime_settings()

        response = self.client.get(reverse("core:home"), HTTP_HOST="mainty.example.com")
        self.assertEqual(response.status_code, 200)

    def test_language_switch_changes_visible_navigation_language(self):
        self.client.force_login(self.viewer_user)

        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("core:dashboard")},
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

        follow_up = self.client.get(reverse("core:dashboard"))
        self.assertContains(follow_up, '<html lang="en">', html=False)
        self.assertContains(follow_up, "Assets")
        self.assertContains(follow_up, "Profile")

    def test_viewer_cannot_access_editor_page(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_access_admin_page(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 403)

    def test_editor_can_access_editor_page(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_access_admin_page(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_editor_page(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("core:editor-demo"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_admin_page(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("core:admin-demo"))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_home_redirects_to_dashboard(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:home"))
        self.assertRedirects(response, reverse("core:dashboard"))

    def test_dashboard_metrics_are_calculated_correctly(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.context["metrics"]["active_assets"], 1)
        self.assertEqual(response.context["metrics"]["maintenance_plans"], 3)
        self.assertEqual(response.context["metrics"]["qualification_plans"], 2)
        self.assertEqual(response.context["metrics"]["open_tasks"], 2)
        self.assertEqual(response.context["metrics"]["overdue_tasks"], 1)
        self.assertEqual(response.context["metrics"]["overdue_maintenance_plans"], 1)
        self.assertEqual(response.context["metrics"]["overdue_qualification_plans"], 1)

    def test_dashboard_context_contains_overdue_items(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))

        overdue_titles = {item.title for item in response.context["overdue_items"]}
        self.assertIn(self.overdue_maintenance.title, overdue_titles)
        self.assertIn(self.overdue_qualification.title, overdue_titles)
        self.assertIn(self.overdue_task.title, overdue_titles)

    def test_dashboard_context_contains_upcoming_items(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))

        upcoming_titles = {item.title for item in response.context["upcoming_items"]}
        self.assertIn(self.upcoming_maintenance.title, upcoming_titles)
        self.assertIn(self.upcoming_qualification.title, upcoming_titles)
        self.assertIn(self.upcoming_task.title, upcoming_titles)

    @override_settings(TASK_DASHBOARD_WARNING_DAYS=2)
    def test_dashboard_uses_configured_task_warning_days(self):
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("core:dashboard"))

        upcoming_titles = {item.title for item in response.context["upcoming_items"]}
        self.assertEqual(response.context["task_warning_days"], 2)
        self.assertNotIn(self.upcoming_task.title, upcoming_titles)

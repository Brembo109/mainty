from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset
from audit.models import AuditLog
from core.models import SystemSettings
from maintenance.models import MaintenancePlan
from qualification.models import QualificationPlan
from tasks.models import Task


class CoreViewsTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)

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

    def test_settings_values_are_saved_correctly(self):
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
            },
        )

        self.assertRedirects(response, reverse("core:settings"))
        settings = SystemSettings.load()
        self.assertEqual(settings.default_maintenance_warning_days, 9)
        self.assertEqual(settings.default_maintenance_interval_value, 45)
        self.assertEqual(settings.default_qualification_warning_days, 21)
        self.assertEqual(settings.default_qualification_interval_value, 6)

        audit_entry = AuditLog.objects.filter(model_name="SystemSettings").latest("id")
        self.assertEqual(audit_entry.user, self.admin_user)

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

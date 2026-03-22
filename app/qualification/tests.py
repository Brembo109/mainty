from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset
from core.due_dates import DUE_STATUS_WARNING
from core.models import SystemSettings

from .models import QualificationEvent, QualificationPlan


class QualificationPlanModelTests(TestCase):
    def test_due_date_and_status_calculation(self):
        today = timezone.localdate()
        commissioning_date = today - timedelta(days=355)
        asset = Asset.objects.create(
            asset_id="A-3000",
            name="Test Bench",
            commissioning_date=commissioning_date,
        )
        plan = QualificationPlan.objects.create(
            asset=asset,
            title="Annual qualification",
            interval_value=1,
            interval_unit=QualificationPlan.INTERVAL_YEARS,
            warning_days=14,
        )
        QualificationEvent.objects.create(
            plan=plan,
            performed_on=today - timedelta(days=358),
            performed_by="Max Mustermann",
        )

        self.assertEqual(plan.next_due_date, today + timedelta(days=7))
        self.assertEqual(plan.due_status.code, DUE_STATUS_WARNING)


class QualificationViewTests(TestCase):
    def setUp(self):
        self.settings = SystemSettings.load()
        self.settings.default_qualification_interval_value = 9
        self.settings.default_qualification_interval_unit = QualificationPlan.INTERVAL_MONTHS
        self.settings.default_qualification_warning_days = 11
        self.settings.save()

        user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)
        self.admin_user = user_model.objects.create_user("qualification_admin", password="pass-12345")
        self.editor_user = user_model.objects.create_user("qualification_editor", password="pass-12345")
        self.viewer_user = user_model.objects.create_user("qualification_viewer", password="pass-12345")
        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(
            asset_id="A-5000",
            name="Inspection Station",
            location="Plant A",
            department="Quality",
            commissioning_date=date(2024, 1, 10),
        )
        self.plan = QualificationPlan.objects.create(
            asset=self.asset,
            title="Semi annual qualification",
            interval_value=6,
            interval_unit=QualificationPlan.INTERVAL_MONTHS,
            warning_days=14,
            responsible_person="QA Team",
        )

    def test_plan_list_requires_login(self):
        response = self.client.get(reverse("qualification:plan-list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('qualification:plan-list')}")

    def test_viewer_can_access_list_and_detail_but_not_edit_views(self):
        self.client.force_login(self.viewer_user)
        self.assertEqual(self.client.get(reverse("qualification:plan-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("qualification:plan-detail", args=[self.plan.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("qualification:plan-create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("qualification:plan-edit", args=[self.plan.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("qualification:event-create", args=[self.plan.pk])).status_code, 403)

    def test_editor_can_create_plan_and_event(self):
        self.client.force_login(self.editor_user)
        create_plan_response = self.client.post(
            reverse("qualification:plan-create"),
            {
                "asset": self.asset.pk,
                "title": "Annual check",
                "interval_value": 1,
                "interval_unit": QualificationPlan.INTERVAL_YEARS,
                "warning_days": 20,
                "responsible_person": "Editor User",
                "is_active": "on",
                "notes": "Created by editor",
            },
        )
        created_plan = QualificationPlan.objects.get(title="Annual check")
        self.assertRedirects(create_plan_response, reverse("qualification:plan-detail", args=[created_plan.pk]))

        event_response = self.client.post(
            reverse("qualification:event-create", args=[self.plan.pk]),
            {
                "performed_on": "2024-02-01",
                "performed_by": "Editor User",
                "notes": "Completed qualification",
            },
        )
        self.plan.refresh_from_db()
        self.assertRedirects(event_response, reverse("qualification:plan-detail", args=[self.plan.pk]))
        self.assertEqual(self.plan.latest_event.performed_on, date(2024, 2, 1))
        self.assertEqual(self.plan.next_due_date, date(2024, 8, 1))

    def test_admin_can_update_plan_and_event(self):
        event = QualificationEvent.objects.create(plan=self.plan, performed_on=date(2024, 2, 1))
        self.client.force_login(self.admin_user)
        plan_response = self.client.post(
            reverse("qualification:plan-edit", args=[self.plan.pk]),
            {
                "asset": self.asset.pk,
                "title": "Semi annual qualification updated",
                "interval_value": 6,
                "interval_unit": QualificationPlan.INTERVAL_MONTHS,
                "warning_days": 10,
                "responsible_person": "Admin User",
                "notes": "Updated",
            },
        )
        event_response = self.client.post(
            reverse("qualification:event-edit", args=[event.pk]),
            {
                "performed_on": "2024-02-05",
                "performed_by": "Admin User",
                "notes": "Updated event",
            },
        )
        self.plan.refresh_from_db()
        event.refresh_from_db()
        self.assertRedirects(plan_response, reverse("qualification:plan-detail", args=[self.plan.pk]))
        self.assertRedirects(event_response, reverse("qualification:plan-detail", args=[self.plan.pk]))
        self.assertEqual(self.plan.title, "Semi annual qualification updated")
        self.assertEqual(event.performed_on, date(2024, 2, 5))

    def test_search_and_filter_work(self):
        other_asset = Asset.objects.create(asset_id="A-5001", name="Bench", location="Plant B", department="Production")
        QualificationPlan.objects.create(
            asset=other_asset,
            title="Inactive qualification",
            interval_value=12,
            interval_unit=QualificationPlan.INTERVAL_MONTHS,
            warning_days=5,
            is_active=False,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(
            reverse("qualification:plan-list"),
            {"q": "Semi", "location": "Plant A", "active": "active"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.title)
        self.assertNotContains(response, "Inactive qualification")

    def test_create_form_uses_system_settings_as_initial_values(self):
        self.client.force_login(self.editor_user)
        response = self.client.get(reverse("qualification:plan-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["interval_value"], 9)
        self.assertEqual(
            response.context["form"].initial["interval_unit"],
            QualificationPlan.INTERVAL_MONTHS,
        )
        self.assertEqual(response.context["form"].initial["warning_days"], 11)

    def test_create_form_allows_overriding_system_defaults(self):
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("qualification:plan-create"),
            {
                "asset": self.asset.pk,
                "title": "Override qualification defaults",
                "interval_value": 3,
                "interval_unit": QualificationPlan.INTERVAL_WEEKS,
                "warning_days": 2,
                "responsible_person": "Editor User",
                "is_active": "on",
                "notes": "",
            },
        )

        created_plan = QualificationPlan.objects.get(title="Override qualification defaults")
        self.assertRedirects(response, reverse("qualification:plan-detail", args=[created_plan.pk]))
        self.assertEqual(created_plan.interval_value, 3)
        self.assertEqual(created_plan.interval_unit, QualificationPlan.INTERVAL_WEEKS)
        self.assertEqual(created_plan.warning_days, 2)

    def test_changing_settings_does_not_affect_existing_plans(self):
        self.settings.default_qualification_interval_value = 24
        self.settings.save()
        self.plan.refresh_from_db()

        self.assertEqual(self.plan.interval_value, 6)

    def test_plan_list_supports_csv_export(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("qualification:plan-list"), {"export": "csv"})

        content = response.content.decode("utf-8-sig")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Titel", content)
        self.assertIn("Semi annual qualification", content)

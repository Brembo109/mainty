from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from assets.models import Asset
from core.due_dates import DUE_STATUS_INACTIVE, DUE_STATUS_UNKNOWN, DUE_STATUS_WARNING
from qualification.models import QualificationPlan
from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER

from .models import MaintenanceEvent, MaintenancePlan


class MaintenancePlanModelTests(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            asset_id="A-2000",
            name="Mixing System",
            commissioning_date=date(2024, 1, 15),
        )

    def test_next_due_date_uses_latest_event(self):
        plan = MaintenancePlan.objects.create(
            asset=self.asset,
            title="Quarterly inspection",
            interval_value=3,
            interval_unit=MaintenancePlan.INTERVAL_MONTHS,
            warning_days=10,
        )
        MaintenanceEvent.objects.create(plan=plan, performed_on=date(2024, 3, 20))

        self.assertEqual(plan.next_due_date, date(2024, 6, 20))

    def test_next_due_date_falls_back_to_commissioning_date(self):
        plan = MaintenancePlan.objects.create(
            asset=self.asset,
            title="Annual service",
            interval_value=1,
            interval_unit=MaintenancePlan.INTERVAL_YEARS,
            warning_days=30,
        )

        self.assertEqual(plan.next_due_date, date(2025, 1, 15))

    def test_inactive_plan_returns_inactive_status(self):
        plan = MaintenancePlan.objects.create(
            asset=self.asset,
            title="Inactive plan",
            interval_value=30,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=5,
            is_active=False,
        )

        self.assertEqual(plan.due_status.code, DUE_STATUS_INACTIVE)

    def test_missing_date_returns_unknown_status(self):
        asset = Asset.objects.create(asset_id="A-2001", name="Filler")
        plan = MaintenancePlan.objects.create(
            asset=asset,
            title="Plan without baseline",
            interval_value=30,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=5,
        )

        self.assertIsNone(plan.next_due_date)
        self.assertEqual(plan.due_status.code, DUE_STATUS_UNKNOWN)


class MaintenanceViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)
        self.admin_user = user_model.objects.create_user("maintenance_admin", password="pass-12345")
        self.editor_user = user_model.objects.create_user("maintenance_editor", password="pass-12345")
        self.viewer_user = user_model.objects.create_user("maintenance_viewer", password="pass-12345")
        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(
            asset_id="A-4000",
            name="Blister Line",
            location="Plant A",
            department="Production",
            commissioning_date=date(2024, 1, 1),
        )
        self.plan = MaintenancePlan.objects.create(
            asset=self.asset,
            title="Monthly service",
            interval_value=30,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=5,
            responsible_person="Service Team",
        )

    def test_plan_list_requires_login(self):
        response = self.client.get(reverse("maintenance:plan-list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('maintenance:plan-list')}")

    def test_viewer_can_access_list_and_detail_but_not_edit_views(self):
        self.client.force_login(self.viewer_user)
        self.assertEqual(self.client.get(reverse("maintenance:plan-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("maintenance:plan-detail", args=[self.plan.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("maintenance:plan-create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("maintenance:plan-edit", args=[self.plan.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("maintenance:event-create", args=[self.plan.pk])).status_code, 403)

    def test_editor_can_create_plan_and_event(self):
        self.client.force_login(self.editor_user)
        create_plan_response = self.client.post(
            reverse("maintenance:plan-create"),
            {
                "asset": self.asset.pk,
                "title": "Weekly check",
                "interval_value": 7,
                "interval_unit": MaintenancePlan.INTERVAL_DAYS,
                "warning_days": 2,
                "responsible_person": "Editor User",
                "is_active": "on",
                "notes": "Created by editor",
            },
        )
        created_plan = MaintenancePlan.objects.get(title="Weekly check")
        self.assertRedirects(create_plan_response, reverse("maintenance:plan-detail", args=[created_plan.pk]))

        event_response = self.client.post(
            reverse("maintenance:event-create", args=[self.plan.pk]),
            {
                "performed_on": "2024-04-01",
                "performed_by": "Editor User",
                "notes": "Completed",
            },
        )
        self.plan.refresh_from_db()
        self.assertRedirects(event_response, reverse("maintenance:plan-detail", args=[self.plan.pk]))
        self.assertEqual(self.plan.latest_event.performed_on, date(2024, 4, 1))
        self.assertEqual(self.plan.next_due_date, date(2024, 5, 1))

    def test_admin_can_update_plan_and_event(self):
        event = MaintenanceEvent.objects.create(plan=self.plan, performed_on=date(2024, 4, 1))
        self.client.force_login(self.admin_user)
        plan_response = self.client.post(
            reverse("maintenance:plan-edit", args=[self.plan.pk]),
            {
                "asset": self.asset.pk,
                "title": "Monthly service updated",
                "interval_value": 31,
                "interval_unit": MaintenancePlan.INTERVAL_DAYS,
                "warning_days": 6,
                "responsible_person": "Admin User",
                "notes": "Updated",
            },
        )
        event_response = self.client.post(
            reverse("maintenance:event-edit", args=[event.pk]),
            {
                "performed_on": "2024-04-02",
                "performed_by": "Admin User",
                "notes": "Updated event",
            },
        )
        self.plan.refresh_from_db()
        event.refresh_from_db()
        self.assertRedirects(plan_response, reverse("maintenance:plan-detail", args=[self.plan.pk]))
        self.assertRedirects(event_response, reverse("maintenance:plan-detail", args=[self.plan.pk]))
        self.assertEqual(self.plan.title, "Monthly service updated")
        self.assertEqual(event.performed_on, date(2024, 4, 2))

    def test_asset_detail_shows_linked_maintenance_and_qualification_plans(self):
        qualification_plan = QualificationPlan.objects.create(
            asset=self.asset,
            title="Annual qualification",
            interval_value=1,
            interval_unit=QualificationPlan.INTERVAL_YEARS,
            warning_days=14,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("assets:detail", args=[self.asset.pk]))
        self.assertContains(response, self.plan.title)
        self.assertContains(response, qualification_plan.title)

    def test_search_and_filter_work(self):
        other_asset = Asset.objects.create(asset_id="A-4001", name="Mixer", location="Plant B", department="QA")
        MaintenancePlan.objects.create(
            asset=other_asset,
            title="Calibration",
            interval_value=14,
            interval_unit=MaintenancePlan.INTERVAL_DAYS,
            warning_days=2,
            is_active=False,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(
            reverse("maintenance:plan-list"),
            {"q": "Monthly", "location": "Plant A", "active": "active"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.title)
        self.assertNotContains(response, "Calibration")

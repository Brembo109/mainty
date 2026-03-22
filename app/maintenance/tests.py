from datetime import date

from django.test import TestCase
from django.utils import timezone

from assets.models import Asset
from core.due_dates import DUE_STATUS_INACTIVE, DUE_STATUS_UNKNOWN, DUE_STATUS_WARNING

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

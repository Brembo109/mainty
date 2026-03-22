from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from assets.models import Asset
from core.due_dates import DUE_STATUS_WARNING

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

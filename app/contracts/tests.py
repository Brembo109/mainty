from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from assets.models import Asset
from audit.context import audit_context
from audit.models import AuditLog

from .models import MaintenanceContract
from .services import CONTRACT_STATUS_ACTIVE, CONTRACT_STATUS_EXPIRED, CONTRACT_STATUS_WARNING


class MaintenanceContractModelTests(TestCase):
    def test_contract_rejects_end_date_before_start_date(self):
        contract = MaintenanceContract(
            title="Servicevertrag",
            vendor="ACME Service",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() - timedelta(days=1),
            warning_months=3,
        )

        with self.assertRaises(ValidationError) as error:
            contract.full_clean()

        self.assertEqual(
            error.exception.message_dict["end_date"],
            ["Das Enddatum darf nicht vor dem Startdatum liegen."],
        )

    def test_status_and_runtime_are_computed_dynamically(self):
        today = timezone.localdate()
        active_contract = MaintenanceContract(
            title="Aktiver Vertrag",
            vendor="ACME Service",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=120),
            warning_months=3,
        )
        warning_contract = MaintenanceContract(
            title="Warnvertrag",
            vendor="ACME Service",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=20),
            warning_months=3,
        )
        expired_contract = MaintenanceContract(
            title="Abgelaufener Vertrag",
            vendor="ACME Service",
            start_date=today - timedelta(days=365),
            end_date=today - timedelta(days=17),
            warning_months=3,
        )

        self.assertEqual(active_contract.status.code, CONTRACT_STATUS_ACTIVE)
        self.assertEqual(warning_contract.status.code, CONTRACT_STATUS_WARNING)
        self.assertEqual(expired_contract.status.code, CONTRACT_STATUS_EXPIRED)
        self.assertEqual(warning_contract.remaining_runtime_display, "läuft in 20 Tagen aus")
        self.assertEqual(expired_contract.remaining_runtime_display, "seit 17 Tagen abgelaufen")


class MaintenanceContractViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.editor_group, _ = Group.objects.get_or_create(name=ROLE_EDITOR)
        self.viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(username="admin", password="pass-12345")
        self.editor_user = user_model.objects.create_user(username="editor", password="pass-12345")
        self.viewer_user = user_model.objects.create_user(username="viewer", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(
            asset_id="A-1000",
            name="Packaging Line 1",
            status=Asset.STATUS_ACTIVE,
        )
        self.contract = MaintenanceContract.objects.create(
            title="Vollwartung Linie 1",
            contract_number="VT-1000",
            order_number="PO-1000",
            vendor="ACME Service",
            start_date=timezone.localdate() - timedelta(days=60),
            end_date=timezone.localdate() + timedelta(days=45),
            warning_months=3,
            maintenance_frequency=MaintenanceContract.FREQUENCY_ANNUAL,
            notes="Testvertrag",
        )
        self.contract.assets.add(self.asset)
        AuditLog.objects.all().delete()

    def test_viewer_can_access_list_and_detail(self):
        self.client.force_login(self.viewer_user)

        list_response = self.client.get(reverse("contracts:list"))
        detail_response = self.client.get(reverse("contracts:detail", args=[self.contract.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.contract.title)
        self.assertContains(detail_response, self.asset.asset_id)

    def test_viewer_cannot_access_create_edit_or_delete(self):
        self.client.force_login(self.viewer_user)

        create_response = self.client.get(reverse("contracts:create"))
        edit_response = self.client.get(reverse("contracts:edit", args=[self.contract.pk]))
        delete_response = self.client.get(reverse("contracts:delete", args=[self.contract.pk]))

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

    def test_editor_can_create_and_edit_contract_but_not_delete(self):
        self.client.force_login(self.editor_user)

        create_response = self.client.post(
            reverse("contracts:create"),
            {
                "title": "Servicevertrag Linie 2",
                "contract_number": "  VT-2000  ",
                "order_number": " PO-2000 ",
                "vendor": "Service GmbH",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "warning_months": 6,
                "maintenance_frequency": MaintenanceContract.FREQUENCY_SEMI_ANNUAL,
                "assets": [self.asset.pk],
                "notes": "Neu angelegt",
            },
        )

        created_contract = MaintenanceContract.objects.get(contract_number="VT-2000")
        self.assertRedirects(create_response, reverse("contracts:detail", args=[created_contract.pk]))
        self.assertEqual(created_contract.order_number, "PO-2000")
        self.assertEqual(created_contract.assets.get().pk, self.asset.pk)

        edit_response = self.client.post(
            reverse("contracts:edit", args=[created_contract.pk]),
            {
                "title": "Servicevertrag Linie 2 Aktualisiert",
                "contract_number": "VT-2000",
                "order_number": "PO-2000",
                "vendor": "Service GmbH",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "warning_months": 3,
                "maintenance_frequency": MaintenanceContract.FREQUENCY_QUARTERLY,
                "assets": [self.asset.pk],
                "notes": "Aktualisiert",
            },
        )

        created_contract.refresh_from_db()
        self.assertRedirects(edit_response, reverse("contracts:detail", args=[created_contract.pk]))
        self.assertEqual(created_contract.title, "Servicevertrag Linie 2 Aktualisiert")
        self.assertEqual(created_contract.warning_months, 3)

        delete_response = self.client.get(reverse("contracts:delete", args=[created_contract.pk]))
        self.assertEqual(delete_response.status_code, 403)

    def test_admin_can_delete_contract_and_audit_log_is_created(self):
        self.admin_user.profile.user_code = "AD"
        self.admin_user.profile.role = ROLE_ADMIN
        self.admin_user.profile.save()
        self.client.force_login(self.admin_user)

        response = self.client.post(reverse("contracts:delete", args=[self.contract.pk]))

        self.assertRedirects(response, reverse("contracts:list"))
        self.assertFalse(MaintenanceContract.objects.filter(pk=self.contract.pk).exists())
        entry = AuditLog.objects.get(
            model_name="MaintenanceContract",
            object_id=str(self.contract.pk),
            action=AuditLog.ACTION_DELETE,
        )
        self.assertEqual(entry.user, self.admin_user)
        self.assertIn("Vollwartung Linie 1", entry.object_repr)

    def test_asset_assignments_are_logged_in_audit_trail(self):
        self.editor_user.profile.user_code = "ED"
        self.editor_user.profile.role = ROLE_EDITOR
        self.editor_user.profile.save()
        extra_asset = Asset.objects.create(asset_id="A-1001", name="Packaging Line 2", status=Asset.STATUS_ACTIVE)

        with audit_context(user=self.editor_user):
            self.contract.assets.add(extra_asset)

        entry = AuditLog.objects.filter(
            model_name="MaintenanceContract",
            object_id=str(self.contract.pk),
            field_name="assets",
        ).latest("id")
        self.assertEqual(entry.user, self.editor_user)
        self.assertIn("A-1001", entry.new_value)

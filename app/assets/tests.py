from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER

from .models import Asset


class AssetModelTests(TestCase):
    def test_asset_creation(self):
        asset = Asset.objects.create(
            asset_id="A-1000",
            name="Packaging Line 1",
            short_name="PL1",
            status=Asset.STATUS_ACTIVE,
        )

        self.assertEqual(asset.asset_id, "A-1000")
        self.assertEqual(str(asset), "A-1000 - Packaging Line 1")


class AssetViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_group = Group.objects.create(name=ROLE_ADMIN)
        self.editor_group = Group.objects.create(name=ROLE_EDITOR)
        self.viewer_group = Group.objects.create(name=ROLE_VIEWER)

        self.admin_user = user_model.objects.create_user(username="admin", password="pass-12345")
        self.editor_user = user_model.objects.create_user(username="editor", password="pass-12345")
        self.viewer_user = user_model.objects.create_user(username="viewer", password="pass-12345")

        self.admin_user.groups.add(self.admin_group)
        self.editor_user.groups.add(self.editor_group)
        self.viewer_user.groups.add(self.viewer_group)

        self.asset = Asset.objects.create(
            asset_id="A-1000",
            name="Packaging Line 1",
            short_name="PL1",
            category="Line",
            manufacturer="ACME",
            serial_number="SN-1",
            location="Plant A",
            department="Production",
            status=Asset.STATUS_ACTIVE,
        )

    def test_asset_list_requires_login(self):
        response = self.client.get(reverse("assets:list"))
        expected = f"{reverse('accounts:login')}?next={reverse('assets:list')}"
        self.assertRedirects(response, expected)

    def test_viewer_can_access_list_and_detail(self):
        self.client.force_login(self.viewer_user)

        list_response = self.client.get(reverse("assets:list"))
        detail_response = self.client.get(reverse("assets:detail", args=[self.asset.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_viewer_cannot_access_create_or_edit(self):
        self.client.force_login(self.viewer_user)

        create_response = self.client.get(reverse("assets:create"))
        edit_response = self.client.get(reverse("assets:edit", args=[self.asset.pk]))

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_editor_can_create_asset(self):
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("assets:create"),
            {
                "asset_id": "A-2000",
                "name": "Inspection Station",
                "short_name": "IS1",
                "category": "Station",
                "manufacturer": "Mainty",
                "model": "M-1",
                "serial_number": "SN-2000",
                "location": "Plant B",
                "department": "QA",
                "commissioning_date": "2025-01-15",
                "status": Asset.STATUS_ACTIVE,
                "notes": "Created from test",
            },
        )

        created_asset = Asset.objects.get(asset_id="A-2000")
        self.assertRedirects(response, reverse("assets:detail", args=[created_asset.pk]))

    def test_admin_can_edit_asset(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("assets:edit", args=[self.asset.pk]),
            {
                "asset_id": "A-1000",
                "name": "Packaging Line 1 Updated",
                "short_name": "PL1",
                "category": "Line",
                "manufacturer": "ACME",
                "model": "",
                "serial_number": "SN-1",
                "location": "Plant A",
                "department": "Production",
                "commissioning_date": "",
                "status": Asset.STATUS_OUT_OF_SERVICE,
                "notes": "Taken offline",
            },
        )

        self.asset.refresh_from_db()
        self.assertRedirects(response, reverse("assets:detail", args=[self.asset.pk]))
        self.assertEqual(self.asset.status, Asset.STATUS_OUT_OF_SERVICE)
        self.assertEqual(self.asset.name, "Packaging Line 1 Updated")

    def test_search_and_filter_work(self):
        Asset.objects.create(
            asset_id="A-1001",
            name="Compressor",
            location="Plant B",
            department="Utilities",
            status=Asset.STATUS_INACTIVE,
        )
        self.client.force_login(self.viewer_user)
        response = self.client.get(
            reverse("assets:list"),
            {"q": "Packaging", "status": Asset.STATUS_ACTIVE, "location": "Plant A"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Packaging Line 1")
        self.assertNotContains(response, "Compressor")
        self.assertEqual(response.context["result_count"], 1)

    def test_pagination_works(self):
        for index in range(2, 14):
            Asset.objects.create(asset_id=f"A-{1000 + index}", name=f"Asset {index}")

        self.client.force_login(self.viewer_user)
        response = self.client.get(reverse("assets:list"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_unique_asset_id_validation_in_create_view(self):
        self.client.force_login(self.editor_user)
        response = self.client.post(
            reverse("assets:create"),
            {
                "asset_id": "A-1000",
                "name": "Duplicate Asset",
                "status": Asset.STATUS_ACTIVE,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["asset_id"],
            ["Asset mit diesem Wert für das Feld Asset-ID existiert bereits."],
        )

    def test_asset_csv_export_requires_login(self):
        response = self.client.get(reverse("assets:list"), {"export": "csv"})
        expected = f"{reverse('accounts:login')}?next={reverse('assets:list')}%3Fexport%3Dcsv"
        self.assertRedirects(response, expected)

    def test_viewer_can_export_assets_as_csv(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("assets:list"), {"export": "csv"})
        content = response.content.decode("utf-8-sig")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertIn("Asset-ID", content)
        self.assertIn("A-1000", content)

    def test_asset_xlsx_export_contains_expected_columns_and_values(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse("assets:list"), {"export": "xlsx"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook.active

        self.assertEqual(sheet["A1"].value, "Asset-ID")
        self.assertEqual(sheet["B1"].value, "Bezeichnung")
        self.assertEqual(sheet["A2"].value, "A-1000")
        self.assertEqual(sheet["B2"].value, "Packaging Line 1")

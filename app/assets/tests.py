from django.test import TestCase

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

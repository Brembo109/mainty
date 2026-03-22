from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "asset_id",
        "name",
        "short_name",
        "category",
        "location",
        "department",
        "status",
        "commissioning_date",
    )
    list_filter = ("status", "category", "location", "department")
    search_fields = (
        "asset_id",
        "name",
        "short_name",
        "serial_number",
        "manufacturer",
        "model",
        "location",
        "department",
    )
    ordering = ("asset_id",)

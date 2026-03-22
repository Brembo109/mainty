from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company_logo",
        "default_maintenance_interval_value",
        "default_maintenance_interval_unit",
        "default_qualification_interval_value",
        "default_qualification_interval_unit",
        "updated_at",
    )

    def has_add_permission(self, request):
        if SystemSettings.objects.exists():
            return False
        return super().has_add_permission(request)

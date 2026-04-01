from django.contrib import admin

from .models import MaintenanceContract


@admin.register(MaintenanceContract)
class MaintenanceContractAdmin(admin.ModelAdmin):
    list_display = ("title", "contract_number", "vendor", "start_date", "end_date")
    list_filter = ("vendor", "maintenance_frequency")
    search_fields = ("title", "contract_number", "order_number", "vendor")
    filter_horizontal = ("assets",)


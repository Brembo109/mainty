from django.contrib import admin

from .models import QualificationEvent, QualificationPlan


class QualificationEventInline(admin.TabularInline):
    model = QualificationEvent
    extra = 0
    ordering = ("-performed_on", "-id")


@admin.register(QualificationPlan)
class QualificationPlanAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "asset",
        "interval_value",
        "interval_unit",
        "warning_days",
        "is_active",
        "next_due_date",
        "due_status_code",
    )
    list_filter = ("is_active", "interval_unit", "asset__status")
    search_fields = ("title", "asset__asset_id", "asset__name", "responsible_person")
    ordering = ("asset__asset_id", "title")
    inlines = [QualificationEventInline]

    @admin.display(description="Faelligkeitsstatus")
    def due_status_code(self, obj):
        return obj.due_status.label


@admin.register(QualificationEvent)
class QualificationEventAdmin(admin.ModelAdmin):
    list_display = ("plan", "performed_on", "performed_by")
    list_filter = ("performed_on", "plan__asset")
    search_fields = ("plan__title", "plan__asset__asset_id", "performed_by")
    ordering = ("-performed_on", "-id")

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "model_name", "object_repr", "field_name", "action")
    list_filter = ("model_name", "action", "user")
    search_fields = ("object_repr", "object_id")
    ordering = ("-timestamp", "-id")
    readonly_fields = (
        "timestamp",
        "user",
        "action",
        "model_name",
        "object_id",
        "object_repr",
        "field_name",
        "old_value",
        "new_value",
        "change_reason",
    )

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

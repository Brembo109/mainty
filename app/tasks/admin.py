from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "asset",
        "priority",
        "status",
        "due_date",
        "responsible_user",
        "is_overdue",
    )
    list_filter = ("status", "priority", "due_date", "asset", "responsible_user")
    search_fields = ("title", "description", "asset__asset_id", "asset__name", "responsible_user__username")
    ordering = ("due_date", "-created_at")
    autocomplete_fields = ("asset", "responsible_user")

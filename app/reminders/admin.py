from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "recipient_email", "status", "sent_at")
    list_filter = ("notification_type", "status", "sent_at")
    search_fields = ("recipient_email", "subject", "object_id")

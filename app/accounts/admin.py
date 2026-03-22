from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from .roles import get_primary_role


User = get_user_model()

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "primary_role",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    filter_horizontal = ("groups", "user_permissions")

    @admin.display(description="Primary role")
    def primary_role(self, obj):
        return get_primary_role(obj) or "-"


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin):
    list_display = ("name",)

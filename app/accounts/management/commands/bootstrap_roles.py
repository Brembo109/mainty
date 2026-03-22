from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.roles import ROLE_ADMIN, ROLE_EDITOR, ROLE_NAMES, ROLE_VIEWER


class Command(BaseCommand):
    help = "Create the initial mainty roles and assign built-in permissions."

    def handle(self, *args, **options):
        user_model = get_user_model()
        user_content_type = ContentType.objects.get_for_model(user_model)
        group_content_type = ContentType.objects.get_for_model(Group)

        admin_permissions = Permission.objects.filter(
            content_type__in=[user_content_type, group_content_type],
            codename__in=[
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "add_group",
                "change_group",
                "delete_group",
                "view_group",
            ],
        )

        for role_name in ROLE_NAMES:
            group, created = Group.objects.get_or_create(name=role_name)
            if role_name == ROLE_ADMIN:
                group.permissions.set(admin_permissions)
            else:
                group.permissions.clear()

            state = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{state} role: {role_name}"))

        self.stdout.write(self.style.SUCCESS(f"Roles ready: {ROLE_ADMIN}, {ROLE_EDITOR}, {ROLE_VIEWER}"))

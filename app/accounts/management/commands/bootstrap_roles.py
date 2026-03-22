from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from accounts.permissions import assign_default_role_permissions
from accounts.roles import LEGACY_ROLE_EDITOR, ROLE_ADMIN, ROLE_NAMES, ROLE_USER, ROLE_VIEWER


class Command(BaseCommand):
    help = "Create the initial mainty roles and assign built-in permissions."

    def handle(self, *args, **options):
        user_model = get_user_model()
        user_content_type = ContentType.objects.get_for_model(user_model)
        profile_content_type = ContentType.objects.get_for_model(UserProfile)
        group_content_type = ContentType.objects.get_for_model(Group)

        admin_permissions = Permission.objects.filter(
            content_type__in=[user_content_type, profile_content_type, group_content_type],
            codename__in=[
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "add_userprofile",
                "change_userprofile",
                "delete_userprofile",
                "view_userprofile",
                "add_group",
                "change_group",
                "delete_group",
                "view_group",
            ],
        )

        for role_name in ROLE_NAMES:
            group, created = Group.objects.get_or_create(name=role_name)
            state = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{state} role: {role_name}"))

        assign_default_role_permissions()
        Group.objects.get(name=ROLE_ADMIN).permissions.add(*admin_permissions)

        legacy_group = Group.objects.filter(name=LEGACY_ROLE_EDITOR).first()
        if legacy_group:
            user_group = Group.objects.get(name=ROLE_USER)
            for user in legacy_group.user_set.all():
                user.groups.add(user_group)
            legacy_group.delete()
            self.stdout.write(self.style.SUCCESS(f"Migrated legacy role: {LEGACY_ROLE_EDITOR} -> {ROLE_USER}"))

        self.stdout.write(self.style.SUCCESS(f"Roles ready: {ROLE_ADMIN}, {ROLE_USER}, {ROLE_VIEWER}"))

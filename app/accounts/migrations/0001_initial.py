from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1])
    Group = apps.get_model("auth", "Group")
    UserProfile = apps.get_model("accounts", "UserProfile")

    admin_group, _ = Group.objects.get_or_create(name="Admin")
    user_group, _ = Group.objects.get_or_create(name="User")
    viewer_group, _ = Group.objects.get_or_create(name="Viewer")
    legacy_editor_group = Group.objects.filter(name="Editor").first()

    for user in User.objects.all():
        group_names = set(user.groups.values_list("name", flat=True))
        if user.is_superuser or "Admin" in group_names:
            role = "Admin"
            user.groups.add(admin_group)
        elif "User" in group_names or "Editor" in group_names:
            role = "User"
            user.groups.add(user_group)
        elif "Viewer" in group_names:
            role = "Viewer"
            user.groups.add(viewer_group)
        else:
            role = "Viewer"
            user.groups.add(viewer_group)

        UserProfile.objects.get_or_create(user=user, defaults={"role": role})

    if legacy_editor_group is not None:
        legacy_editor_group.delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_code", models.CharField(blank=True, max_length=12, null=True, unique=True, verbose_name="Kürzel")),
                (
                    "role",
                    models.CharField(
                        choices=[("Admin", "Admin"), ("User", "User"), ("Viewer", "Viewer")],
                        default="Viewer",
                        max_length=20,
                        verbose_name="Rolle",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Benutzer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Benutzerprofil",
                "verbose_name_plural": "Benutzerprofile",
                "ordering": ["user__last_name", "user__first_name", "user__username"],
            },
        ),
        migrations.RunPython(create_profiles_for_existing_users, migrations.RunPython.noop),
    ]

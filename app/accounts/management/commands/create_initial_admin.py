from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserProfile
from accounts.roles import ROLE_ADMIN


class Command(BaseCommand):
    help = "Create or update an initial admin user and assign the Admin role."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        admin_group = Group.objects.filter(name=ROLE_ADMIN).first()
        if admin_group is None:
            raise CommandError(
                "Admin role does not exist. Run 'python manage.py bootstrap_roles' first."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=options["username"],
            defaults={"email": options["email"]},
        )
        user.email = options["email"]
        user.is_staff = True
        user.is_superuser = True
        user.set_password(options["password"])
        user.save()
        user.groups.add(admin_group)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = ROLE_ADMIN
        profile.save()

        state = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{state} admin user: {user.username}"))

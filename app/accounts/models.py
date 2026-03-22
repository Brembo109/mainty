from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _

from .roles import LEGACY_ROLE_EDITOR, ROLE_ADMIN, ROLE_USER, ROLE_VIEWER


class UserProfile(models.Model):
    ROLE_CHOICES = (
        (ROLE_ADMIN, _("Admin")),
        (ROLE_USER, _("User")),
        (ROLE_VIEWER, _("Viewer")),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("Benutzer"),
    )
    user_code = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Kürzel"),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER,
        verbose_name=_("Rolle"),
    )

    class Meta:
        ordering = ["user__last_name", "user__first_name", "user__username"]
        verbose_name = _("Benutzerprofil")
        verbose_name_plural = _("Benutzerprofile")

    def __str__(self) -> str:
        name = self.user.get_full_name().strip() or self.user.username
        if self.user_code:
            return f"{name} [{self.user_code}]"
        return name

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        if getattr(self, "_skip_role_sync", False):
            return result
        self.sync_role_membership()
        return result

    def sync_role_membership(self):
        target_groups = [Group.objects.get_or_create(name=self.role)[0]]
        self.user.groups.set(target_groups)

        legacy_editor_group = Group.objects.filter(name=LEGACY_ROLE_EDITOR).first()
        if legacy_editor_group:
            self.user.groups.remove(legacy_editor_group)

        should_be_staff = self.role == ROLE_ADMIN or self.user.is_superuser
        if self.user.is_staff != should_be_staff:
            self.user.is_staff = should_be_staff
            self.user.save(update_fields=["is_staff"])


def infer_role_from_user(user) -> str:
    group_names = set(user.groups.values_list("name", flat=True))
    if ROLE_ADMIN in group_names or user.is_superuser:
        return ROLE_ADMIN
    if ROLE_USER in group_names or LEGACY_ROLE_EDITOR in group_names:
        return ROLE_USER
    if ROLE_VIEWER in group_names:
        return ROLE_VIEWER
    return ROLE_VIEWER

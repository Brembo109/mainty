from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .permissions import assign_default_role_permissions
from .models import UserProfile, infer_role_from_user
from .roles import ROLE_NAMES


User = get_user_model()


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile(user=instance, role=infer_role_from_user(instance))
        profile._skip_role_sync = True
        profile.save()
        return

    profile, _ = UserProfile.objects.get_or_create(
        user=instance,
        defaults={"role": infer_role_from_user(instance)},
    )
    desired_role = infer_role_from_user(instance)
    if profile.role != desired_role:
        profile.role = desired_role
        profile.save(update_fields=["role"])


@receiver(post_save, sender=Group)
def ensure_default_role_permissions(sender, instance, created, **kwargs):
    if created and instance.name in ROLE_NAMES:
        assign_default_role_permissions()

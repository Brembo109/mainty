from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile, infer_role_from_user


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

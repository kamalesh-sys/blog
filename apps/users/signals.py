from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.common.email_notifications import send_activity_email
from .models import Follow

User = get_user_model()

def get_display_text(user):
    if user.display_name:
        return user.display_name
    return user.username

@receiver(post_save, sender=Follow)
def send_follow_email_notification(sender, instance, created, **kwargs):
    if not created:
        return

    recipient_email = instance.following.email
    if not recipient_email:
        return

    follower_name = get_display_text(instance.follower)
    send_activity_email(
        subject=f"{follower_name} started following you",
        message=f"{follower_name} followed you.",
        recipient_list=[recipient_email],
    )

@receiver(pre_save, sender=User)
def mark_profile_pic_change(sender, instance, **kwargs):
    instance._profile_pic_updated = False

    if instance._state.adding or not instance.pk:
        return

    old_profile_pic = sender.objects.filter(pk=instance.pk).values_list("profile_pic", flat=True).first()
    if old_profile_pic != instance.profile_pic:
        instance._profile_pic_updated = True

@receiver(post_save, sender=User)
def send_profile_pic_email_notification(sender, instance, created, **kwargs):
    if created:
        return

    if not getattr(instance, "_profile_pic_updated", False):
        return

    if not instance.email:
        return

    user_name = get_display_text(instance)
    send_activity_email(
        subject=f"{user_name} updated profile picture",
        message=f"{user_name} updated profile picture.",
        recipient_list=[instance.email],
    )

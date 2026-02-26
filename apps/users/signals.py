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

def has_profile_picture_changed(user):
    is_new_user = user._state.adding or user.pk is None
    if is_new_user:
        return False

    existing_user = User.objects.filter(pk=user.pk).values("profile_pic").first()
    if existing_user:
        previous_profile_picture = existing_user["profile_pic"]
    else:
        previous_profile_picture = None

    if previous_profile_picture != user.profile_pic:
        return True
    return False


@receiver(pre_save, sender=User)
def mark_profile_pic_change(sender, instance, **kwargs):
    profile_picture_changed = has_profile_picture_changed(instance)

    if profile_picture_changed:
        instance.profile_picture_updated = True
    else:
        instance.profile_picture_updated = False
    
@receiver(post_save, sender=User)
def send_profile_pic_email_notification(sender, instance, created, **kwargs):
    if created:
        return

    profile_picture_updated = getattr(instance, "profile_picture_updated", False)
    if not profile_picture_updated:
        return

    if not instance.email:
        return

    username_tag = f"@{instance.username}"
    send_activity_email(
        subject="Your account has an updated profile picture",
        message=f"Your account, {username_tag}, has an updated profile picture.",
        recipient_list=[instance.email],
    )

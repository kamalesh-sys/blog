from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common.email_notifications import send_activity_email
from .models import Comment, Post, PostLike


def get_display_text(user):
    if user.display_name:
        return user.display_name
    return user.username


@receiver(post_save, sender=Post)
def send_new_post_email_notification(sender, instance, created, **kwargs):
    if not created:
        return

    author = instance.author
    author_name = get_display_text(author)
    post_name = instance.name
    post_content = (instance.content or "").strip()
    message = f'{author_name} published a new post: "{post_name}".'
    if post_content:
        message += f'\n\nPost content:\n"{post_content}"'

    follower_emails = author.followers.values_list("email", flat=True)
    for follower_email in follower_emails:
        if not follower_email:
            continue

        send_activity_email(
            subject=f"{author_name} published a new post",
            message=message,
            recipient_list=[follower_email],
        )


@receiver(post_save, sender=PostLike)
def send_post_like_email_notification(sender, instance, created, **kwargs):
    if not created:
        return

    post_author = instance.post.author
    if post_author.id == instance.user_id:
        return

    if not post_author.email:
        return

    liker_name = get_display_text(instance.user)
    send_activity_email(
        subject=f"{liker_name} liked your post",
        message=f'{liker_name} liked your post "{instance.post.name}".',
        recipient_list=[post_author.email],
    )


@receiver(post_save, sender=Comment)
def send_post_comment_email_notification(sender, instance, created, **kwargs):
    if not created:
        return

    post_author = instance.post.author
    commenter = instance.author
    if post_author.id == commenter.id:
        return

    if not post_author.email:
        return

    commenter_name = get_display_text(commenter)
    post_name = instance.post.name
    comment_text = (instance.content or "").strip()
    message = f'{commenter_name} commented on your post "{post_name}".'
    if comment_text:
        message += f'\n\nComment:\n"{comment_text}"'

    send_activity_email(
        subject=f"{commenter_name} commented on your post",
        message=message,
        recipient_list=[post_author.email],
    )

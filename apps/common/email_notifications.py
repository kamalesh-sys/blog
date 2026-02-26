from django.conf import settings
from django.core.mail import send_mail


def send_activity_email(subject, message, recipient_list):
    recipients = [email for email in recipient_list if email]
    if not recipients:
        return 0

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )

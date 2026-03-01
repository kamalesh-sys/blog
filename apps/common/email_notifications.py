from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from threading import Thread


def _send_activity_email(subject, message, recipients):
    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )


def send_activity_email(subject, message, recipient_list):
    recipients = []
    for email in recipient_list:
        if email:
            recipients.append(email)

    if not recipients:
        return 0

    use_async = getattr(settings, "EMAIL_SEND_ASYNC", False)
    if not use_async:
        return _send_activity_email(subject, message, recipients)

    def enqueue_email_send():
        Thread(
            target=_send_activity_email,
            args=(subject, message, recipients),
            daemon=True,
        ).start()

    transaction.on_commit(enqueue_email_send)
    return len(recipients)

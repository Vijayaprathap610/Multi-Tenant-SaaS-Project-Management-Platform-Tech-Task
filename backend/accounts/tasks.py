from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_password_reset_email(user_id):
    """Takes only the user id; the token is generated here so it is never put in the broker or logs."""
    user = get_user_model().objects.filter(pk=user_id, is_active=True,
                                           is_platform_admin=False).first()
    if user is None:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    send_mail("Reset your Tech Task password",
              f"Use this link to choose a new password (valid for one hour):\n{link}\n\n"
              "If you did not request this, ignore this email.",
              settings.DEFAULT_FROM_EMAIL, [user.email])

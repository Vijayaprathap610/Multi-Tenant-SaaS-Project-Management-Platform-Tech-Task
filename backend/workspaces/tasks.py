from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .invites import make_token
from .models import Invitation


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_invitation_email(invitation_id):
    """Receives only the id; the signed token is rebuilt here so it never sits in the broker."""
    inv = Invitation.objects.select_related("workspace").filter(
        pk=invitation_id, accepted_at__isnull=True, revoked_at__isnull=True).first()
    if inv is None:
        return
    link = f"{settings.FRONTEND_URL}/accept-invite?token={make_token(inv)}"
    send_mail(
        subject=f"You're invited to {inv.workspace.name} on Tech Task",
        message=f"You have been invited as {inv.get_role_display()}.\n\nAccept: {link}\n",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[inv.email],
    )


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_member_welcome_email(membership_id):
    from .models import Membership

    membership = Membership.objects.select_related("workspace", "user").filter(pk=membership_id).first()
    if membership is None:
        return
    user = membership.user
    ws = membership.workspace
    role_display = membership.get_role_display()
    login_url = f"{settings.FRONTEND_URL}/login"
    reset_url = f"{settings.FRONTEND_URL}/forgot-password"

    subject = f"Welcome to {ws.name} on Tech Task - Account Created"
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        f"Your account has been created for company '{ws.name}' on Tech Task with the role of {role_display}.\n\n"
        f"Company: {ws.name}\n"
        f"Role: {role_display}\n"
        f"Designation: {membership.designation or 'Not specified'}\n\n"
        f"You can log in to your account here:\n{login_url}\n\n"
        f"If you need to set or reset your password, please use the secure password recovery link:\n{reset_url}\n\n"
        f"Best regards,\nTech Task Team\n"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@shared_task
def prune_invitations(days=30):
    """Scheduled maintenance: delete invitations that expired, were revoked or were accepted long ago."""
    from datetime import timedelta

    from django.db.models import Q
    from django.utils import timezone
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = Invitation.objects.filter(
        Q(expires_at__lt=cutoff) | Q(revoked_at__lt=cutoff) | Q(accepted_at__lt=cutoff)).delete()
    return deleted

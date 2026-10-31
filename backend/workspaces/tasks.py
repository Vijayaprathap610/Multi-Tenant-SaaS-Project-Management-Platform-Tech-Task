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

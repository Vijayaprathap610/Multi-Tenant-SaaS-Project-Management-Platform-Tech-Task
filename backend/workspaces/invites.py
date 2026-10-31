from django.core import signing
from django.utils import timezone

from .models import Invitation

SALT = "techtask.invitation"
MAX_AGE = 7 * 24 * 3600


def make_token(invitation):
    return signing.dumps(str(invitation.pk), salt=SALT)


def resolve(token):
    """Return the pending, unexpired Invitation for this token, else None."""
    try:
        pk = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature:  # includes SignatureExpired
        return None
    inv = Invitation.objects.select_related("workspace").filter(pk=pk).first()
    if inv is None or inv.accepted_at or inv.revoked_at or inv.expires_at <= timezone.now():
        return None
    return inv

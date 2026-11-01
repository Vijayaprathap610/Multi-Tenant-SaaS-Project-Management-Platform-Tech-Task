import uuid

from django.conf import settings
from django.db import models

from tenancy.models import TenantModel


class Role(models.TextChoices):
    OWNER = "owner", "Workspace Owner"
    ADMIN = "admin", "Workspace Administrator"
    PROJECT_MANAGER = "project_manager", "Project Manager"
    MEMBER = "member", "Developer / Team Member"


class Workspace(models.Model):
    """The tenant. One company = one workspace in v1 (decision D1)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    designation = models.CharField(max_length=100, blank=True, default="")
    contact_number = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "user"],
                                               name="unique_membership")]
        indexes = [models.Index(fields=["user", "workspace"])]


ALL_ROLES = {r.value for r in Role}
MANAGE_ROLES = {Role.OWNER.value, Role.ADMIN.value}
INVITABLE_ROLES = [Role.ADMIN, Role.PROJECT_MANAGER, Role.MEMBER]  # Owner is never invitable


class Invitation(TenantModel):
    """Token is a signed, expiring value derived from `id` (see invites.py); it is never stored."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                   related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["workspace", "email"])]

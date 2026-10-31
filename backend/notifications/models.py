import uuid

from django.conf import settings
from django.db import models

from tenancy.models import TenantModel


class Notification(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    event_type = models.CharField(max_length=64)
    message = models.CharField(max_length=300)
    issue = models.ForeignKey("issues.Issue", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    project_id = models.UUIDField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=64)  # event id: retries can never create duplicates
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["recipient", "dedupe_key"], name="unique_notification_event")]
        indexes = [models.Index(fields=["recipient", "workspace", "read_at", "-created_at"])]

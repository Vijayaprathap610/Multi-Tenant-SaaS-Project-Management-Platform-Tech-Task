import uuid

from django.conf import settings
from django.db import models

from tenancy.models import TenantModel

EVENTS = ["issue.created", "issue.assigned", "issue.status_changed", "issue.deleted", "comment.created",
          "attachment.uploaded", "sprint.started", "sprint.completed", "ping"]


class WebhookEndpoint(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    description = models.CharField(max_length=200, blank=True)
    events = models.JSONField(default=list)  # subset of EVENTS, or ["*"]
    # Needed to sign requests, so stored recoverably. Shown once on create/rotate, never returned
    # by any other endpoint or written to logs. (Field-level encryption is a documented next step.)
    secret = models.CharField(max_length=64, editable=False)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)


class DeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class WebhookDelivery(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_id = models.UUIDField()
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True)  # class name / HTTP code only
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["endpoint", "event_id"], name="unique_delivery_per_event")]
        indexes = [models.Index(fields=["endpoint", "-created_at"])]

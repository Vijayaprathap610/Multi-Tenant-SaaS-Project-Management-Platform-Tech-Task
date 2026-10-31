import uuid

from django.db import models
from django.db.models import Q


class Subscription(models.Model):
    """At most one per workspace. No row (or an inactive one) means the Free plan."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField("workspaces.Workspace", on_delete=models.CASCADE, related_name="subscription")
    plan = models.CharField(max_length=20, default="free")
    status = models.CharField(max_length=30, default="inactive")  # Stripe status, or "inactive" before checkout
    stripe_customer_id = models.CharField(max_length=64, blank=True)
    stripe_subscription_id = models.CharField(max_length=64, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["stripe_customer_id"],
                                               condition=~Q(stripe_customer_id=""),
                                               name="unique_stripe_customer")]


class StripeEvent(models.Model):
    """Processed webhook event ids: makes duplicate deliveries harmless."""
    id = models.CharField(max_length=80, primary_key=True)
    type = models.CharField(max_length=80)
    received_at = models.DateTimeField(auto_now_add=True)

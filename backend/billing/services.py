from datetime import datetime, timezone as dt_tz

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from audit.services import record

from .models import Subscription
from .plans import PLANS, plan_for_price

ENTITLED_STATUSES = {"active", "trialing", "past_due"}  # past_due keeps access during Stripe's retry window


class InvalidWebhook(Exception):
    pass


def get_stripe():
    import stripe  # imported lazily so the rest of the app works without the package configured
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def construct_event(payload, sig_header):
    """Verifies the Stripe signature; any failure becomes InvalidWebhook."""
    try:
        return get_stripe().Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise InvalidWebhook() from exc


def effective_plan(workspace):
    sub = Subscription.objects.filter(workspace=workspace).first()
    if sub and sub.status in ENTITLED_STATUSES and sub.plan in PLANS:
        return sub.plan
    return "free"


def usage_for(workspace, include_pending_invites=True):
    from attachments.models import Attachment
    from projects.models import Project
    from webhooks.models import WebhookEndpoint
    from workspaces.models import Invitation, Membership

    members = Membership.objects.filter(workspace=workspace).count()
    if include_pending_invites:
        members += Invitation.objects.filter(workspace=workspace, accepted_at__isnull=True,
                                             revoked_at__isnull=True, expires_at__gt=timezone.now()).count()
    storage = Attachment.objects.filter(workspace=workspace).aggregate(s=Sum("size"))["s"] or 0
    return {"members": members, "projects": Project.objects.filter(workspace=workspace).count(),
            "storage_bytes": storage, "webhooks": WebhookEndpoint.objects.filter(workspace=workspace).count()}


def enforce_limit(workspace, resource, *, add=1, include_pending_invites=True):
    """resource: members | projects | webhooks | storage (add = bytes for storage)."""
    plan_key = effective_plan(workspace)
    limits = PLANS[plan_key]
    usage = usage_for(workspace, include_pending_invites)
    if resource == "storage":
        cap = None if limits["storage_mb"] is None else limits["storage_mb"] * 1024 * 1024
        current = usage["storage_bytes"]
    else:
        cap, current = limits[resource], usage[resource]
    if cap is not None and current + add > cap:
        raise PermissionDenied({"detail": f"The {limits['name']} plan limit for {resource} has been reached. "
                                          "Upgrade your plan to continue.",
                                "code": "plan_limit", "resource": resource})


def _ts(value):
    return datetime.fromtimestamp(value, tz=dt_tz.utc) if value else None


def sync_subscription(stripe_sub):
    """Apply a Stripe subscription object to our row. Stripe is authoritative. Unknown
    subscriptions/customers are ignored: we only trust rows we created ourselves at checkout."""
    sub = (Subscription.objects.filter(stripe_subscription_id=stripe_sub["id"]).first()
           or Subscription.objects.filter(stripe_customer_id=stripe_sub.get("customer", "")).exclude(
               stripe_customer_id="").first())
    if sub is None:
        return None
    items = (stripe_sub.get("items") or {}).get("data") or [{}]
    price = (items[0].get("price") or {}).get("id")
    sub.stripe_subscription_id = stripe_sub["id"]
    sub.status = stripe_sub["status"]
    sub.plan = plan_for_price(price) or sub.plan
    sub.current_period_end = _ts(stripe_sub.get("current_period_end") or items[0].get("current_period_end"))
    sub.cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))
    sub.save()
    record("billing.subscription_updated", workspace=sub.workspace,
           metadata={"plan": sub.plan, "status": sub.status, "cancel_at_period_end": sub.cancel_at_period_end})
    return sub


def handle_event(event):
    obj = event["data"]["object"]
    kind = event["type"]
    if kind == "checkout.session.completed":
        sub = (Subscription.objects.filter(workspace_id=obj.get("client_reference_id")).first()
               or Subscription.objects.filter(stripe_customer_id=obj.get("customer") or "none").first())
        if sub is None or not obj.get("subscription"):
            return
        fields_to_update = ["stripe_subscription_id"]
        if not sub.stripe_customer_id and obj.get("customer"):
            sub.stripe_customer_id = obj["customer"]
            fields_to_update.append("stripe_customer_id")
        sub.stripe_subscription_id = obj["subscription"]
        sub.save(update_fields=fields_to_update)
        sync_subscription(get_stripe().Subscription.retrieve(obj["subscription"]))
    elif kind in ("customer.subscription.created", "customer.subscription.updated",
                  "customer.subscription.deleted"):
        sync_subscription(obj)

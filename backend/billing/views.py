from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import record
from tenancy.mixins import TenantScopedMixin
from workspaces.models import MANAGE_ROLES, Role

from .models import StripeEvent, Subscription
from .plans import PLANS, price_id
from .services import (ENTITLED_STATUSES, InvalidWebhook, construct_event, effective_plan, get_stripe,
                       handle_event, usage_for)

OWNER_ONLY = {Role.OWNER.value}


def _limits_payload(plan_key):
    p = PLANS[plan_key]
    return {k: p[k] for k in ("members", "projects", "storage_mb", "webhooks")}


class BillingStatusView(TenantScopedMixin, APIView):
    required_roles = {"GET": MANAGE_ROLES}

    def get(self, request, **kwargs):
        ws = request.membership.workspace
        sub = Subscription.objects.filter(workspace=ws).first()
        plan_key = effective_plan(ws)
        u = usage_for(ws)
        return Response({
            "plan": plan_key, "plan_name": PLANS[plan_key]["name"],
            "status": sub.status if sub else "inactive",
            "current_period_end": sub.current_period_end if sub else None,
            "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
            "limits": _limits_payload(plan_key),
            "usage": {"members": u["members"], "projects": u["projects"], "webhooks": u["webhooks"],
                      "storage_mb": round(u["storage_bytes"] / (1024 * 1024), 2)},
            "plans": [{"key": k, "name": v["name"], "limits": _limits_payload(k)} for k, v in PLANS.items()],
            "can_manage": request.membership.role == Role.OWNER,
            "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
            "demo_mode": not bool(settings.STRIPE_SECRET_KEY),
        })


class CheckoutView(TenantScopedMixin, APIView):
    required_roles = {"POST": OWNER_ONLY}

    def post(self, request, **kwargs):
        ws = request.membership.workspace
        plan = request.data.get("plan")
        if plan not in ("pro", "business"):
            raise ValidationError({"detail": "This plan is not available for checkout."})

        has_stripe = bool(settings.STRIPE_SECRET_KEY and price_id(plan))
        use_demo = request.data.get("demo", False) or not has_stripe

        sub, _ = Subscription.objects.get_or_create(workspace=ws)

        if not use_demo:
            if sub.status in ENTITLED_STATUSES and sub.stripe_subscription_id and not sub.stripe_subscription_id.startswith("demo_"):
                raise ValidationError({"detail": "Use the billing portal to change an existing subscription."})
            stripe = get_stripe()
            if not sub.stripe_customer_id:
                customer = stripe.Customer.create(email=request.user.email, metadata={"workspace_id": str(ws.id)})
                sub.stripe_customer_id = customer.id
                sub.save(update_fields=["stripe_customer_id"])
            session = stripe.checkout.Session.create(
                mode="subscription", customer=sub.stripe_customer_id,
                line_items=[{"price": price_id(plan), "quantity": 1}], client_reference_id=str(ws.id),
                success_url=f"{settings.FRONTEND_URL}/app/billing?checkout=success",
                cancel_url=f"{settings.FRONTEND_URL}/app/billing?checkout=cancelled")
            record("billing.checkout_started", actor=request.user, workspace=ws, metadata={"plan": plan})
            return Response({"url": session.url})
        else:
            # Demo Payment Gateway simulation
            sub.plan = plan
            sub.status = "active"
            sub.current_period_end = timezone.now() + timedelta(days=30)
            sub.cancel_at_period_end = False
            if not sub.stripe_customer_id:
                sub.stripe_customer_id = f"demo_cus_{ws.id}"
            sub.stripe_subscription_id = f"demo_sub_{ws.id}_{plan}"
            sub.save()
            record("billing.checkout_completed", actor=request.user, workspace=ws, metadata={"plan": plan, "gateway": "demo"})
            return Response({
                "url": f"{settings.FRONTEND_URL}/app/billing?checkout=success",
                "success": True,
                "demo": True,
                "plan": plan
            })


class PortalView(TenantScopedMixin, APIView):
    required_roles = {"POST": OWNER_ONLY}

    def post(self, request, **kwargs):
        sub = Subscription.objects.filter(workspace=request.membership.workspace).exclude(
            stripe_customer_id="").first()
        if sub is None:
            raise ValidationError({"detail": "No billing account exists yet. Start a subscription first."})
        if not settings.STRIPE_SECRET_KEY or (sub.stripe_customer_id and sub.stripe_customer_id.startswith("demo_")):
            return Response({"url": f"{settings.FRONTEND_URL}/app/billing?portal=demo"})
        session = get_stripe().billing_portal.Session.create(
            customer=sub.stripe_customer_id, return_url=f"{settings.FRONTEND_URL}/app/billing")
        return Response({"url": session.url})


class CancelView(TenantScopedMixin, APIView):
    required_roles = {"POST": OWNER_ONLY}

    def post(self, request, **kwargs):
        ws = request.membership.workspace
        sub = Subscription.objects.filter(workspace=ws).exclude(stripe_subscription_id="").first()
        if sub is None or sub.status not in ENTITLED_STATUSES:
            raise ValidationError({"detail": "There is no active subscription to cancel."})
        immediate = request.data.get("immediate", False)
        if immediate:
            sub.plan = "free"
            sub.status = "inactive"
            sub.cancel_at_period_end = False
            sub.save()
            record("billing.subscription_cancelled_immediate", actor=request.user, workspace=ws)
            return Response({"cancel_at_period_end": False, "plan": "free"})
        if settings.STRIPE_SECRET_KEY and not sub.stripe_subscription_id.startswith("demo_"):
            get_stripe().Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
        sub.cancel_at_period_end = True
        sub.save(update_fields=["cancel_at_period_end"])
        record("billing.cancel_requested", actor=request.user, workspace=ws)
        return Response({"cancel_at_period_end": True})


class StripeWebhookView(APIView):
    """Public by necessity; authenticity comes solely from Stripe's signature."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []  # Stripe may burst; authenticity is the signature, not the rate

    def post(self, request):
        try:
            event = construct_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""))
        except InvalidWebhook:
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():  # a failure rolls back the event record so Stripe retries
            _, created = StripeEvent.objects.get_or_create(id=event["id"], defaults={"type": event["type"]})
            if not created:
                return Response({"status": "duplicate"})
            handle_event(event)
        return Response({"status": "ok"})

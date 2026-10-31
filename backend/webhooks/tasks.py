from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .delivery import attempt, mark_delivered
from .models import DeliveryStatus, WebhookDelivery, WebhookEndpoint

MAX_ATTEMPTS = 5


def backoff(attempts):
    return min(30 * 2 ** (attempts - 1), 3600)  # 30s, 1m, 2m, 4m ...


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def dispatch_event(event_id, event_type, workspace_id, payload):
    """Fan an event out to this workspace's subscribed endpoints only. The unique
    (endpoint, event_id) constraint makes re-running this task safe."""
    for ep in WebhookEndpoint.objects.filter(workspace_id=workspace_id, active=True):
        if "*" not in ep.events and event_type not in ep.events:
            continue
        delivery, created = WebhookDelivery.objects.get_or_create(
            endpoint=ep, event_id=event_id,
            defaults=dict(workspace_id=ep.workspace_id, event_type=event_type, payload=payload))
        if created:
            deliver_webhook.delay(str(delivery.pk))


@shared_task
def deliver_webhook(delivery_id):
    """Retries with exponential backoff up to MAX_ATTEMPTS; finished deliveries are never re-sent.
    Receivers can de-duplicate on the X-TechTask-Delivery header."""
    delivery = WebhookDelivery.objects.select_related("endpoint").filter(pk=delivery_id).first()
    if delivery is None or delivery.status != DeliveryStatus.PENDING:
        return
    ok, status, error = attempt(delivery)
    delivery.attempts += 1
    delivery.response_status = status
    delivery.error = error
    if ok:
        delivery.status = DeliveryStatus.SUCCESS
        mark_delivered(delivery)
    elif delivery.attempts >= MAX_ATTEMPTS or error in ("UnsafeTarget", "TenantMismatch"):
        delivery.status = DeliveryStatus.FAILED
    delivery.save()
    if delivery.status == DeliveryStatus.PENDING:
        deliver_webhook.apply_async(args=[str(delivery.pk)], countdown=backoff(delivery.attempts))


@shared_task
def prune_deliveries(days=30):
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = WebhookDelivery.objects.filter(created_at__lt=cutoff).exclude(
        status=DeliveryStatus.PENDING).delete()
    return deleted

import uuid

from django.db import transaction


def emit(event_type, *, workspace_id, actor=None, issue=None, data=None):
    """Single entry point for domain events. After the surrounding transaction commits it
    enqueues (a) in-app/email notifications and (b) outgoing webhook deliveries.
    Task arguments carry ids and small public fields only, never secrets."""
    event_id = str(uuid.uuid4())
    payload = {"workspace_id": str(workspace_id), **(data or {})}
    actor_id = getattr(actor, "pk", None)
    issue_id = str(issue.pk) if issue is not None else None

    def _enqueue():
        from notifications.tasks import notify_event
        from webhooks.tasks import dispatch_event
        notify_event.delay(event_id, event_type, str(workspace_id), issue_id, actor_id, payload)
        dispatch_event.delay(event_id, event_type, str(workspace_id), payload)

    transaction.on_commit(_enqueue)
    return event_id

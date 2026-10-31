from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from issues.models import Issue
from projects.access import user_has_project_access

from .models import Notification

User = get_user_model()

TEMPLATES = {
    "issue.assigned": "{actor} assigned {key} to you",
    "issue.status_changed": "{actor} moved {key} to {to}",
    "comment.created": "{actor} commented on {key}",
}


def _recipients(event_type, issue):
    if event_type == "issue.assigned":
        return [issue.assignee]
    if event_type in ("issue.status_changed", "comment.created"):
        return [issue.reporter, issue.assignee]
    return []


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def notify_event(event_id, event_type, workspace_id, issue_id, actor_id, payload):
    """Tenant-safe: the issue must belong to the stated workspace, and every recipient must still
    have access to that project, so nothing can leak across tenants. Idempotent per (recipient, event)."""
    if event_type not in TEMPLATES or not issue_id:
        return
    issue = (Issue.objects.select_related("project", "assignee", "reporter")
             .filter(pk=issue_id, workspace_id=workspace_id).first())
    if issue is None:
        return
    actor = User.objects.filter(pk=actor_id).first()
    message = TEMPLATES[event_type].format(actor=actor.email if actor else "Someone", key=issue.key,
                                           to=payload.get("to", ""))
    seen = set()
    for user in _recipients(event_type, issue):
        if user is None or user.pk == actor_id or user.pk in seen:
            continue
        seen.add(user.pk)
        if not user_has_project_access(user.pk, issue.project):
            continue
        _, created = Notification.objects.get_or_create(
            recipient=user, dedupe_key=event_id,
            defaults=dict(workspace_id=issue.workspace_id, event_type=event_type, message=message,
                          issue=issue, project_id=issue.project_id))
        if created and settings.NOTIFY_BY_EMAIL:
            send_mail(f"Tech Task: {issue.key}", message, settings.DEFAULT_FROM_EMAIL, [user.email])


@shared_task
def prune_notifications(days=90):
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = Notification.objects.filter(read_at__isnull=False, created_at__lt=cutoff).delete()
    return deleted

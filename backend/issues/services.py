from rest_framework.exceptions import ValidationError

from audit.services import record
from workflows.models import WorkflowTransition

from .models import Issue


def check_transition(project, from_status, to_status):
    """The one place workflow rules are enforced; used by PATCH and by the Kanban move."""
    if from_status.pk == to_status.pk:
        return
    if not WorkflowTransition.objects.filter(project=project, from_status=from_status,
                                             to_status=to_status).exists():
        raise ValidationError({"status": f"Transition from '{from_status.name}' to "
                                         f"'{to_status.name}' is not allowed."})


def position_for(project, status, before_issue_id, exclude_pk=None):
    """Position that places an issue before `before_issue_id` in a column, or at the end."""
    qs = Issue.objects.filter(project=project, status=status).order_by("position", "pk")
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if before_issue_id is None:
        last = qs.last()
        return last.position + 1 if last else 1.0
    before = qs.filter(pk=before_issue_id).first()
    if before is None:
        raise ValidationError({"before_issue_id": "Not found in the target column."})
    prev = qs.filter(position__lt=before.position).last()
    return (prev.position + before.position) / 2 if prev else before.position - 1


def audit_status_change(actor, issue, old_status, new_status):
    record("issue.status_changed", actor=actor, workspace=issue.workspace, resource=issue,
           metadata={"from": old_status.name, "to": new_status.name, "key": issue.key})

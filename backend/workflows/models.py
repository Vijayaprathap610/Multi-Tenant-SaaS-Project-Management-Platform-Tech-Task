import uuid

from django.db import models

from tenancy.models import TenantModel


class StatusCategory(models.TextChoices):
    TODO = "todo", "To do"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"


class WorkflowStatus(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="statuses")
    name = models.CharField(max_length=60)
    category = models.CharField(max_length=12, choices=StatusCategory.choices)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [models.UniqueConstraint(fields=["project", "name"], name="unique_status_name")]


class WorkflowTransition(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="transitions")
    from_status = models.ForeignKey(WorkflowStatus, on_delete=models.CASCADE, related_name="outgoing")
    to_status = models.ForeignKey(WorkflowStatus, on_delete=models.CASCADE, related_name="incoming")

    class Meta:
        # Self-transitions are rejected in TransitionSerializer. (A DB CheckConstraint is
        # deliberately avoided: its keyword changed between Django 5.0 and 5.1.)
        constraints = [models.UniqueConstraint(fields=["from_status", "to_status"],
                                               name="unique_transition")]

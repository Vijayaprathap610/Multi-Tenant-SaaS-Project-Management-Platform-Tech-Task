import uuid

from django.db import models

from tenancy.models import TenantModel


class Board(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="boards")
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)


class BoardColumn(TenantModel):
    """A column shows the issues in one workflow status; dropping a card here is a transition."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=60)
    status = models.ForeignKey("workflows.WorkflowStatus", on_delete=models.CASCADE, related_name="+")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["board", "status"], name="unique_column_status")]

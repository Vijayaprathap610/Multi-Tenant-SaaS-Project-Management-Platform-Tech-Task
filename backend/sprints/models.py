import uuid

from django.db import models
from django.db.models import Q

from tenancy.models import TenantModel


class SprintStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"


class Sprint(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="sprints")
    name = models.CharField(max_length=120)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=SprintStatus.choices, default=SprintStatus.PLANNED)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["project", "status"])]
        constraints = [models.UniqueConstraint(fields=["project"], condition=Q(status="active"),
                                               name="one_active_sprint_per_project")]

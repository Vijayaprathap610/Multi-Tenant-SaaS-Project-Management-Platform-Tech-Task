import uuid

from django.conf import settings
from django.db import models

from tenancy.models import TenantModel


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Issue(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="issues")
    number = models.PositiveIntegerField(editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.ForeignKey("workflows.WorkflowStatus", on_delete=models.PROTECT, related_name="issues")
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="+")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                 related_name="+")
    sprint = models.ForeignKey("sprints.Sprint", null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="issues")
    labels = models.JSONField(default=list, blank=True)
    due_date = models.DateField(null=True, blank=True)
    position = models.FloatField(default=0)  # order within a column
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "number"], name="unique_issue_number")]
        indexes = [
            models.Index(fields=["workspace", "project", "status", "position"]),
            models.Index(fields=["project", "assignee"]),
            models.Index(fields=["project", "sprint"]),
        ]

    @property
    def key(self):
        return f"{self.project.key}-{self.number}"

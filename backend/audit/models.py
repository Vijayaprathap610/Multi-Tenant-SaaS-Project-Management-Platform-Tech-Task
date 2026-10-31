from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Append-only record. Never put passwords, tokens or secrets in `metadata`."""
    workspace = models.ForeignKey("workspaces.Workspace", null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="+")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    event_type = models.CharField(max_length=64, db_index=True)
    resource_type = models.CharField(max_length=64, blank=True)
    resource_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["workspace", "-created_at"])]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("Audit events are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit events cannot be deleted.")

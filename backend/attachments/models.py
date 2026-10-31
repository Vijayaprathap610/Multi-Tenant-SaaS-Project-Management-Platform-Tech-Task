import uuid

from django.conf import settings
from django.db import models

from tenancy.models import TenantModel


def attachment_path(instance, filename):
    # Random storage name; the client-supplied filename never touches the filesystem.
    return f"{instance.workspace_id}/{uuid.uuid4().hex}"


class Attachment(TenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="+")
    issue = models.ForeignKey("issues.Issue", on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                    related_name="+")
    file = models.FileField(upload_to=attachment_path, max_length=255)
    original_name = models.CharField(max_length=200)  # sanitized, display/download name only
    content_type = models.CharField(max_length=100)   # decided server-side from the extension map
    size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["issue", "created_at"])]

from django.db import models


class TenantModel(models.Model):
    """Base class for every tenant-owned table (projects, issues, ...).

    The workspace FK is mandatory and set server-side from the verified
    membership, never from request data.
    """
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.CASCADE,
                                  related_name="+", editable=False)

    class Meta:
        abstract = True

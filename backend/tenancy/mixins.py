from rest_framework.permissions import IsAuthenticated

from .permissions import WorkspaceMembershipPermission


class TenantScopedMixin:
    """Put first in the MRO of every tenant-owned view.

    Queryset is always filtered by the verified membership's workspace and
    creates always stamp that workspace. Serializers must NOT expose `workspace`.
    """
    permission_classes = [IsAuthenticated, WorkspaceMembershipPermission]

    def get_queryset(self):
        return super().get_queryset().filter(workspace_id=self.request.membership.workspace_id)

    def perform_create(self, serializer):
        serializer.save(workspace=self.request.membership.workspace)

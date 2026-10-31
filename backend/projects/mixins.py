from rest_framework.permissions import IsAuthenticated

from tenancy.mixins import TenantScopedMixin

from .permissions import ProjectAccessPermission


class ProjectScopedMixin(TenantScopedMixin):
    permission_classes = [IsAuthenticated, ProjectAccessPermission]
    project_filter_field = "project_id"  # override when the model reaches project via a relation

    def get_queryset(self):
        return super().get_queryset().filter(**{self.project_filter_field: self.request.project.pk})

    def perform_create(self, serializer):
        serializer.save(workspace=self.request.membership.workspace, project=self.request.project)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["project"] = getattr(self.request, "project", None)
        return ctx

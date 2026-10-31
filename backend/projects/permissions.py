from rest_framework.exceptions import NotFound

from tenancy.permissions import WorkspaceMembershipPermission

from .access import has_project_access
from .models import Project


class ProjectAccessPermission(WorkspaceMembershipPermission):
    """Workspace membership + role check, then project scope. The project is looked up
    inside the verified workspace only, so a project id from another tenant is a 404."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        project = Project.objects.filter(pk=view.kwargs["project_id"],
                                         workspace_id=request.membership.workspace_id).first()
        if project is None or not has_project_access(request.membership, project):
            raise NotFound()
        request.project = project
        return True

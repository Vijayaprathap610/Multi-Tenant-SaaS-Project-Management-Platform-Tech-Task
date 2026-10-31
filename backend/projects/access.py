from workspaces.models import MANAGE_ROLES, Membership

from .models import ProjectMember


def has_project_access(membership, project):
    """Owners/Admins see every project in their workspace; PMs and Members only
    the projects they were explicitly added to."""
    if membership.role in MANAGE_ROLES:
        return True
    return ProjectMember.objects.filter(project=project, user_id=membership.user_id).exists()


def user_has_project_access(user_id, project):
    m = Membership.objects.filter(workspace_id=project.workspace_id, user_id=user_id).first()
    return bool(m and has_project_access(m, project))

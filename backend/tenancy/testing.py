from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from workspaces.models import Membership, Role, Workspace

User = get_user_model()
PW = "pw-Str0ng-123!x"


def make_user(email):
    return User.objects.create_user(email, PW)


def make_tenant(name, owner_email, **extra_members):
    """extra_members: role -> email. Returns (workspace, {role: user})."""
    owner = make_user(owner_email)
    ws = Workspace.objects.create(name=name, slug=name.lower(), created_by=owner)
    Membership.objects.create(workspace=ws, user=owner, role=Role.OWNER)
    users = {Role.OWNER.value: owner}
    for role, email in extra_members.items():
        u = make_user(email)
        Membership.objects.create(workspace=ws, user=u, role=role)
        users[role] = u
    return ws, users


class BaseAPITest(APITestCase):
    def setUp(self):
        cache.clear()  # reset throttle counters between tests


def make_project(ws, creator, key="PRJ", members=()):
    from projects.models import Project, ProjectMember
    from projects.services import create_project_defaults
    p = Project.objects.create(workspace=ws, name=f"Project {key}", key=key, created_by=creator)
    for u in (creator, *members):
        ProjectMember.objects.create(workspace=ws, project=p, user=u)
    create_project_defaults(p)
    return p


def make_issue(project, reporter, title="Issue", status_name="To Do", **kw):
    from issues.models import Issue
    from workflows.models import WorkflowStatus
    project.issue_counter += 1
    project.save(update_fields=["issue_counter"])
    status = WorkflowStatus.objects.get(project=project, name=status_name)
    return Issue.objects.create(workspace_id=project.workspace_id, project=project,
                                number=project.issue_counter, title=title, status=status,
                                reporter=reporter, position=float(project.issue_counter), **kw)


def purl(ws, project, path=""):
    return f"/api/workspaces/{ws.id}/projects/{project.id}/{path}"


def make_pro(ws):
    """Give a workspace the Pro plan (tests that exceed Free limits)."""
    from billing.models import Subscription
    return Subscription.objects.create(workspace=ws, plan="pro", status="active")

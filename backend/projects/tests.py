from audit.models import AuditEvent
from boards.models import Board
from tenancy.testing import BaseAPITest, make_issue, make_project, make_tenant, purl
from workflows.models import WorkflowStatus, WorkflowTransition
from workspaces.models import Membership

from .models import Project, ProjectMember


class ProjectTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", admin="ad@a.test", project_manager="pm@a.test",
                                 member="m@a.test")
        self.owner, self.admin, self.pm, self.member = (u["owner"], u["admin"], u["project_manager"],
                                                        u["member"])
        self.list_url = f"/api/workspaces/{self.ws.id}/projects/"

    def _create(self, key="WEB", user=None):
        self.client.force_authenticate(user or self.owner)
        return self.client.post(self.list_url, {"name": "Website", "key": key}, format="json")

    def test_create_seeds_workflow_board_and_membership(self):
        r = self._create()
        self.assertEqual(r.status_code, 201)
        p = Project.objects.get(key="WEB")
        self.assertEqual(WorkflowStatus.objects.filter(project=p).count(), 3)
        self.assertEqual(WorkflowTransition.objects.filter(project=p).count(), 4)
        self.assertEqual(Board.objects.get(project=p).columns.count(), 3)
        self.assertTrue(ProjectMember.objects.filter(project=p, user=self.owner).exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="project.created", workspace=self.ws).exists())

    def test_duplicate_and_invalid_key_rejected(self):
        self._create("WEB")
        self.assertEqual(self._create("WEB").status_code, 400)
        self.assertEqual(self._create("web").status_code, 400)

    def test_pm_and_member_cannot_create_projects(self):
        self.assertEqual(self._create("AAA", self.pm).status_code, 403)
        self.assertEqual(self._create("BBB", self.member).status_code, 403)

    def test_pm_only_sees_assigned_projects(self):
        self._create("WEB")
        p = Project.objects.get(key="WEB")
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.get(self.list_url).json()["results"], [])
        self.assertEqual(self.client.get(f"{self.list_url}{p.id}/").status_code, 404)

        self.client.force_authenticate(self.owner)
        mid = Membership.objects.get(workspace=self.ws, user=self.pm).id
        r = self.client.post(f"{self.list_url}{p.id}/members/", {"membership_id": str(mid)}, format="json")
        self.assertEqual(r.status_code, 201)
        self.client.force_authenticate(self.pm)
        self.assertEqual(len(self.client.get(self.list_url).json()["results"]), 1)
        self.assertEqual(self.client.get(f"{self.list_url}{p.id}/").status_code, 200)

    def test_admin_sees_all_projects(self):
        self._create("WEB")
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get(self.list_url).json()["results"]), 1)

    def test_role_rules_for_update_and_delete(self):
        p = make_project(self.ws, self.owner, "WEB", members=[self.pm, self.member])
        url = f"{self.list_url}{p.id}/"
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.patch(url, {"description": "x"}, format="json").status_code, 403)
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.patch(url, {"description": "x"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(url, {"key": "NEW"}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_cannot_add_user_from_another_workspace_as_project_member(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        p = make_project(self.ws, self.owner, "WEB")
        foreign = Membership.objects.get(workspace=ws_b, user=ub["owner"])
        self.client.force_authenticate(self.owner)
        r = self.client.post(f"{self.list_url}{p.id}/members/", {"membership_id": str(foreign.id)}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(ProjectMember.objects.filter(project=p, user=ub["owner"]).exists())


class ProjectCrossTenantTests(BaseAPITest):
    """Tenant A's owner calls tenant B's ids directly through the API."""

    def setUp(self):
        super().setUp()
        self.ws_a, ua = make_tenant("A", "oa@a.test")
        self.ws_b, ub = make_tenant("B", "ob@b.test")
        self.owner_a = ua["owner"]
        self.proj_b = make_project(self.ws_b, ub["owner"], "BEE")
        self.issue_b = make_issue(self.proj_b, ub["owner"], "secret b issue")
        self.board_b = Board.objects.get(project=self.proj_b)
        self.client.force_authenticate(self.owner_a)

    def test_project_listing_in_foreign_workspace_is_404(self):
        r = self.client.get(f"/api/workspaces/{self.ws_b.id}/projects/")
        self.assertEqual(r.status_code, 404)

    def test_foreign_project_id_under_own_workspace_is_404_for_every_subresource(self):
        for path in ("", "members/", "statuses/", "transitions/", "boards/", "sprints/", "issues/",
                     f"boards/{self.board_b.id}/kanban/", f"issues/{self.issue_b.id}/"):
            r = self.client.get(purl(self.ws_a, self.proj_b, path))
            self.assertEqual(r.status_code, 404, path)
            self.assertNotIn("secret b issue", r.content.decode())

    def test_writes_against_foreign_project_are_404_and_change_nothing(self):
        url = purl(self.ws_a, self.proj_b, "issues/")
        self.assertEqual(self.client.post(url, {"title": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.patch(url + f"{self.issue_b.id}/", {"title": "hacked"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url + f"{self.issue_b.id}/").status_code, 404)
        self.assertEqual(self.client.post(url + f"{self.issue_b.id}/move/", {}, format="json").status_code, 404)
        self.assertEqual(self.client.patch(purl(self.ws_a, self.proj_b), {"name": "hacked"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(purl(self.ws_a, self.proj_b)).status_code, 404)
        self.issue_b.refresh_from_db()
        self.assertEqual(self.issue_b.title, "Issue")
        self.assertTrue(Project.objects.filter(pk=self.proj_b.pk).exists())

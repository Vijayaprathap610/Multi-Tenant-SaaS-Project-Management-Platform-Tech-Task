from django.db import connection
from django.test.utils import CaptureQueriesContext

from audit.models import AuditEvent
from boards.models import Board
from tenancy.testing import BaseAPITest, make_issue, make_project, make_tenant, make_user, purl
from workflows.models import WorkflowStatus
from workspaces.models import Membership, Role

from .models import Issue


class IssueBase(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", admin="ad@a.test", project_manager="pm@a.test",
                                 member="m@a.test", **{})
        self.owner, self.pm, self.member = u["owner"], u["project_manager"], u["member"]
        self.outsider = make_user("out@a.test")  # workspace member without project access
        Membership.objects.create(workspace=self.ws, user=self.outsider, role=Role.MEMBER)
        self.project = make_project(self.ws, self.owner, "PRJ", members=[self.pm, self.member])
        self.st = {s.name: s for s in WorkflowStatus.objects.filter(project=self.project)}
        self.url = purl(self.ws, self.project, "issues/")


class IssueCrudTests(IssueBase):
    def test_create_assigns_key_default_status_reporter_and_audits(self):
        self.client.force_authenticate(self.member)
        r = self.client.post(self.url, {"title": "First", "priority": "high", "labels": ["bug"]}, format="json")
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["key"], "PRJ-1")
        self.assertEqual(body["status"], str(self.st["To Do"].id))
        self.assertEqual(body["reporter_email"], "m@a.test")
        r2 = self.client.post(self.url, {"title": "Second"}, format="json")
        self.assertEqual(r2.json()["key"], "PRJ-2")
        self.assertTrue(AuditEvent.objects.filter(event_type="issue.created", workspace=self.ws).exists())

    def test_client_cannot_set_reporter_number_or_workspace(self):
        self.client.force_authenticate(self.member)
        r = self.client.post(self.url, {"title": "x", "number": 99, "reporter": self.owner.id,
                                        "workspace": "00000000-0000-0000-0000-000000000000"}, format="json")
        self.assertEqual(r.status_code, 201)
        issue = Issue.objects.get()
        self.assertEqual((issue.number, issue.reporter_id, issue.workspace_id),
                         (1, self.member.id, self.ws.id))

    def test_outsider_without_project_access_gets_404(self):
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_member_can_delete_only_own_issues_pm_can_delete_any(self):
        mine = make_issue(self.project, self.member, "mine")
        theirs = make_issue(self.project, self.owner, "theirs")
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.delete(f"{self.url}{theirs.id}/").status_code, 403)
        self.assertEqual(self.client.delete(f"{self.url}{mine.id}/").status_code, 204)
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.delete(f"{self.url}{theirs.id}/").status_code, 204)

    def test_foreign_ids_in_body_are_rejected(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        proj_b = make_project(ws_b, ub["owner"], "BEE")
        foreign_status = WorkflowStatus.objects.filter(project=proj_b).first()
        self.client.force_authenticate(self.owner)
        r = self.client.post(self.url, {"title": "x", "status": str(foreign_status.id)}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(self.url, {"title": "x", "assignee": ub["owner"].id}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Issue.objects.count(), 0)

    def test_assignee_must_have_project_access(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post(self.url, {"title": "x", "assignee": self.outsider.id}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(self.url, {"title": "x", "assignee": self.member.id}, format="json")
        self.assertEqual(r.status_code, 201)

    def test_filter_search_order_and_pagination(self):
        make_issue(self.project, self.owner, "Login bug", priority="high")
        make_issue(self.project, self.owner, "Docs", priority="low")
        self.client.force_authenticate(self.owner)
        body = self.client.get(self.url, {"priority": "high"}).json()
        self.assertEqual([i["title"] for i in body["results"]], ["Login bug"])
        self.assertEqual(self.client.get(self.url, {"q": "doc"}).json()["count"], 1)
        titles = [i["title"] for i in self.client.get(self.url, {"ordering": "title"}).json()["results"]]
        self.assertEqual(titles, ["Docs", "Login bug"])
        self.assertEqual(self.client.get(self.url, {"status": "not-a-uuid"}).status_code, 400)
        self.assertIn("count", body)

    def test_status_with_issues_cannot_be_deleted(self):
        make_issue(self.project, self.owner)
        self.client.force_authenticate(self.pm)
        r = self.client.delete(purl(self.ws, self.project, f"statuses/{self.st['To Do'].id}/"))
        self.assertEqual(r.status_code, 400)


class WorkflowEnforcementTests(IssueBase):
    def test_disallowed_transition_rejected_on_patch_and_move_and_nothing_changes(self):
        issue = make_issue(self.project, self.owner)
        done = str(self.st["Done"].id)
        self.client.force_authenticate(self.owner)
        r = self.client.patch(f"{self.url}{issue.id}/", {"status": done}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"{self.url}{issue.id}/move/", {"status": done}, format="json")
        self.assertEqual(r.status_code, 400)
        issue.refresh_from_db()
        self.assertEqual(issue.status, self.st["To Do"])

    def test_allowed_transition_works_and_is_audited(self):
        issue = make_issue(self.project, self.owner)
        self.client.force_authenticate(self.member)
        r = self.client.patch(f"{self.url}{issue.id}/", {"status": str(self.st["In Progress"].id)}, format="json")
        self.assertEqual(r.status_code, 200)
        ev = AuditEvent.objects.get(event_type="issue.status_changed")
        self.assertEqual((ev.metadata["from"], ev.metadata["to"]), ("To Do", "In Progress"))

    def test_pm_can_open_a_new_transition_member_cannot(self):
        issue = make_issue(self.project, self.owner)
        body = {"from_status": str(self.st["To Do"].id), "to_status": str(self.st["Done"].id)}
        turl = purl(self.ws, self.project, "transitions/")
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(turl, body, format="json").status_code, 403)
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.post(turl, body, format="json").status_code, 201)
        self.assertEqual(self.client.post(turl, body, format="json").status_code, 400)  # duplicate
        r = self.client.post(f"{self.url}{issue.id}/move/", {"status": body["to_status"]}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_self_transition_rejected(self):
        sid = str(self.st["To Do"].id)
        self.client.force_authenticate(self.pm)
        r = self.client.post(purl(self.ws, self.project, "transitions/"),
                             {"from_status": sid, "to_status": sid}, format="json")
        self.assertEqual(r.status_code, 400)


class KanbanTests(IssueBase):
    def setUp(self):
        super().setUp()
        self.board = Board.objects.get(project=self.project)
        self.kanban = purl(self.ws, self.project, f"boards/{self.board.id}/kanban/")

    def _column(self, name):
        cols = self.client.get(self.kanban).json()["columns"]
        return [i["key"] for c in cols if c["name"] == name for i in c["issues"]]

    def test_move_persists_status_and_order(self):
        i1, i2, i3 = (make_issue(self.project, self.owner, f"i{n}") for n in (1, 2, 3))
        self.client.force_authenticate(self.member)
        self.assertEqual(self._column("To Do"), ["PRJ-1", "PRJ-2", "PRJ-3"])
        r = self.client.post(f"{self.url}{i3.id}/move/",
                             {"status": str(self.st["To Do"].id), "before_issue_id": str(i1.id)}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._column("To Do"), ["PRJ-3", "PRJ-1", "PRJ-2"])
        r = self.client.post(f"{self.url}{i1.id}/move/", {"status": str(self.st["In Progress"].id)}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._column("In Progress"), ["PRJ-1"])
        self.assertEqual(self._column("To Do"), ["PRJ-3", "PRJ-2"])
        i1.refresh_from_db()
        self.assertEqual(i1.status, self.st["In Progress"])

    def test_move_with_bad_before_issue_is_rejected(self):
        i1 = make_issue(self.project, self.owner)
        self.client.force_authenticate(self.owner)
        r = self.client.post(f"{self.url}{i1.id}/move/", {"status": str(self.st["In Progress"].id),
                             "before_issue_id": "00000000-0000-0000-0000-000000000001"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_kanban_query_count_does_not_grow_with_issue_count(self):
        self.client.force_authenticate(self.owner)
        for n in range(3):
            make_issue(self.project, self.owner, f"a{n}", assignee=self.member)
        with CaptureQueriesContext(connection) as few:
            self.assertEqual(self.client.get(self.kanban).status_code, 200)
        for n in range(15):
            make_issue(self.project, self.owner, f"b{n}", assignee=self.pm if n % 2 else self.member)
        with CaptureQueriesContext(connection) as many:
            self.assertEqual(self.client.get(self.kanban).status_code, 200)
        self.assertEqual(len(few), len(many))

    def test_column_status_must_belong_to_project_and_be_unique(self):
        curl = purl(self.ws, self.project, f"boards/{self.board.id}/columns/")
        self.client.force_authenticate(self.pm)
        r = self.client.post(curl, {"name": "dup", "status": str(self.st["Done"].id), "position": 9}, format="json")
        self.assertEqual(r.status_code, 400)  # already has a column
        extra = self.client.post(purl(self.ws, self.project, "statuses/"),
                                 {"name": "Review", "category": "in_progress", "position": 5}, format="json")
        self.assertEqual(extra.status_code, 201)
        r = self.client.post(curl, {"name": "Review", "status": extra.json()["id"], "position": 3}, format="json")
        self.assertEqual(r.status_code, 201)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(curl, {"name": "x", "status": extra.json()["id"]}, format="json").status_code, 403)

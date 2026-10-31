from datetime import date, timedelta

from audit.models import AuditEvent
from issues.models import Issue
from issues.tests import IssueBase
from tenancy.testing import make_issue, make_project, make_tenant, purl


class SprintTests(IssueBase):
    def setUp(self):
        super().setUp()
        self.surl = purl(self.ws, self.project, "sprints/")
        today = date.today()
        self.body = {"name": "Sprint 1", "start_date": str(today), "end_date": str(today + timedelta(days=14))}

    def _sprint(self, **over):
        self.client.force_authenticate(self.pm)
        r = self.client.post(self.surl, {**self.body, **over}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["id"]

    def test_date_validation_and_permissions(self):
        self.client.force_authenticate(self.pm)
        bad = {**self.body, "end_date": str(date.today() - timedelta(days=1))}
        self.assertEqual(self.client.post(self.surl, bad, format="json").status_code, 400)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(self.surl, self.body, format="json").status_code, 403)
        self.assertEqual(self.client.get(self.surl).status_code, 200)

    def test_only_one_active_sprint_and_status_not_client_settable(self):
        s1 = self._sprint()
        s2 = self._sprint(name="Sprint 2")
        self.client.patch(f"{self.surl}{s1}/", {"status": "completed"}, format="json")
        self.assertEqual(self.client.get(f"{self.surl}{s1}/").json()["status"], "planned")
        self.assertEqual(self.client.post(f"{self.surl}{s1}/start/").status_code, 200)
        self.assertEqual(self.client.post(f"{self.surl}{s2}/start/").status_code, 400)
        self.assertEqual(self.client.post(f"{self.surl}{s1}/start/").status_code, 400)
        self.assertTrue(AuditEvent.objects.filter(event_type="sprint.started").exists())

    def test_complete_moves_unfinished_to_backlog_and_keeps_done(self):
        sid = self._sprint()
        todo = make_issue(self.project, self.owner, "todo")
        done = make_issue(self.project, self.owner, "done", status_name="Done")
        r = self.client.post(f"{self.surl}{sid}/issues/", {"issue_ids": [str(todo.id), str(done.id)]}, format="json")
        self.assertEqual(r.json(), {"assigned": 2})
        self.client.post(f"{self.surl}{sid}/start/")
        report = self.client.get(f"{self.surl}{sid}/report/").json()
        self.assertEqual((report["total_issues"], report["by_category"]["done"], report["completion_rate"]), (2, 1, 0.5))
        r = self.client.post(f"{self.surl}{sid}/complete/", {}, format="json")
        self.assertEqual((r.status_code, r.json()["incomplete_moved"]), (200, 1))
        todo.refresh_from_db(); done.refresh_from_db()
        self.assertIsNone(todo.sprint_id)
        self.assertEqual(str(done.sprint_id), sid)
        self.assertEqual(self.client.patch(f"{self.surl}{sid}/", {"name": "x"}, format="json").status_code, 400)

    def test_complete_can_roll_over_to_a_planned_sprint(self):
        s1, s2 = self._sprint(), self._sprint(name="Sprint 2")
        i = make_issue(self.project, self.owner, sprint=Issue._meta.get_field("sprint").related_model.objects.get(pk=s1))
        self.client.post(f"{self.surl}{s1}/start/")
        r = self.client.post(f"{self.surl}{s1}/complete/", {"move_incomplete_to": s2}, format="json")
        self.assertEqual(r.status_code, 200)
        i.refresh_from_db()
        self.assertEqual(str(i.sprint_id), s2)

    def test_bulk_assign_rejects_foreign_issue_ids_atomically(self):
        sid = self._sprint()
        mine = make_issue(self.project, self.owner, "mine")
        ws_b, ub = make_tenant("B", "ob@b.test")
        theirs = make_issue(make_project(ws_b, ub["owner"], "BEE"), ub["owner"], "theirs")
        r = self.client.post(f"{self.surl}{sid}/issues/", {"issue_ids": [str(mine.id), str(theirs.id)]}, format="json")
        self.assertEqual(r.status_code, 400)
        mine.refresh_from_db(); theirs.refresh_from_db()
        self.assertIsNone(mine.sprint_id)
        self.assertIsNone(theirs.sprint_id)

    def test_cannot_assign_issue_to_completed_sprint_via_patch(self):
        sid = self._sprint()
        self.client.post(f"{self.surl}{sid}/start/")
        self.client.post(f"{self.surl}{sid}/complete/", {}, format="json")
        issue = make_issue(self.project, self.owner)
        r = self.client.patch(f"{self.url}{issue.id}/", {"sprint": sid}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_only_planned_sprints_can_be_deleted(self):
        sid = self._sprint()
        self.client.post(f"{self.surl}{sid}/start/")
        self.assertEqual(self.client.delete(f"{self.surl}{sid}/").status_code, 400)

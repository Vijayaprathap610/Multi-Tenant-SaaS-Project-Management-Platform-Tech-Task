from issues.tests import IssueBase
from projects.models import ProjectMember
from tenancy.testing import make_issue, make_project, make_tenant, purl

from .models import Report, ReportStatus
from .tasks import generate_project_report


class ReportTests(IssueBase):
    def setUp(self):
        super().setUp()
        self.rurl = purl(self.ws, self.project, "reports/")
        make_issue(self.project, self.owner, "a", priority="high")
        make_issue(self.project, self.owner, "b", status_name="Done")

    def test_pm_requests_report_task_computes_it(self):
        self.client.force_authenticate(self.pm)
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(self.rurl, {}, format="json")
        self.assertEqual(r.status_code, 202)
        report = self.client.get(f"{self.rurl}{r.json()['id']}/").json()
        self.assertEqual(report["status"], "ready")
        self.assertEqual((report["data"]["total_issues"], report["data"]["done_issues"],
                          report["data"]["completion_rate"]), (2, 1, 0.5))

    def test_member_cannot_request_or_read_reports(self):
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(self.rurl, {}, format="json").status_code, 403)
        self.assertEqual(self.client.get(self.rurl).status_code, 403)

    def test_task_rechecks_requester_access_and_is_idempotent(self):
        report = Report.objects.create(workspace=self.ws, project=self.project, requested_by=self.pm)
        ProjectMember.objects.filter(project=self.project, user=self.pm).delete()
        generate_project_report(str(report.id))
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.FAILED)
        self.assertEqual(report.data, {})
        generate_project_report(str(report.id))  # second run is a no-op
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.FAILED)

    def test_csv_export_is_scoped_and_formula_safe(self):
        make_issue(self.project, self.owner, "=HYPERLINK(\"http://evil\")")
        other = make_project(self.ws, self.owner, "OTH")
        make_issue(other, self.owner, "other project issue")
        self.client.force_authenticate(self.pm)
        r = self.client.get(self.rurl + "export/issues/")
        body = b"".join(r.streaming_content).decode()
        self.assertEqual(r.status_code, 200)
        self.assertIn("PRJ-1", body)
        self.assertNotIn("other project issue", body)
        self.assertIn("'=HYPERLINK", body)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get(self.rurl + "export/issues/").status_code, 403)

    def test_foreign_project_report_and_export_are_404(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        proj_b = make_project(ws_b, ub["owner"], "BEE")
        make_issue(proj_b, ub["owner"], "secret b")
        self.client.force_authenticate(self.owner)
        for path in ("reports/", "reports/export/issues/"):
            self.assertEqual(self.client.get(purl(self.ws, proj_b, path)).status_code, 404)
        self.assertEqual(self.client.post(purl(self.ws, proj_b, "reports/"), {}, format="json").status_code, 404)

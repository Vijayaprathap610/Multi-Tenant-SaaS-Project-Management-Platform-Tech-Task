"""Systematic cross-tenant matrix for the collaboration modules: tenant A's Owner calls every
tenant-B resource id directly, both under A's own workspace URL and under B's."""
import json
import tempfile

from django.core.files.base import ContentFile
from django.test import override_settings

from attachments.models import Attachment
from audit.models import AuditEvent
from comments.models import Comment
from notifications.models import Notification
from reports.models import Report
from tenancy.testing import BaseAPITest, make_issue, make_project, make_tenant
from webhooks.models import WebhookEndpoint


class CrossTenantCollaborationTests(BaseAPITest):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._override = override_settings(MEDIA_ROOT=cls._tmp.name)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        cls._tmp.cleanup()

    def setUp(self):
        super().setUp()
        self.ws_a, ua = make_tenant("A", "oa@a.test")
        self.ws_b, ub = make_tenant("B", "ob@b.test")
        self.owner_a, self.owner_b = ua["owner"], ub["owner"]
        self.proj_b = make_project(self.ws_b, self.owner_b, "BEE")
        self.issue_b = make_issue(self.proj_b, self.owner_b, "confidential-title")
        self.comment_b = Comment.objects.create(workspace=self.ws_b, project=self.proj_b, issue=self.issue_b,
                                                author=self.owner_b, body="confidential-comment")
        self.att_b = Attachment(workspace=self.ws_b, project=self.proj_b, issue=self.issue_b,
                                uploaded_by=self.owner_b, original_name="confidential.txt",
                                content_type="text/plain", size=4, sha256="0" * 64)
        self.att_b.file.save("x", ContentFile(b"data"), save=False)
        self.att_b.save()
        self.hook_b = WebhookEndpoint.objects.create(workspace=self.ws_b, url="https://b.example.com/h",
                                                     events=["*"], secret="whsec_confidential")
        self.report_b = Report.objects.create(workspace=self.ws_b, project=self.proj_b,
                                              requested_by=self.owner_b, data={"x": "confidential-report"})
        self.note_b = Notification.objects.create(workspace=self.ws_b, recipient=self.owner_b, event_type="x",
                                                  message="confidential-note", dedupe_key="b")
        AuditEvent.objects.create(workspace=self.ws_b, event_type="confidential.event")
        self.client.force_authenticate(self.owner_a)

    def _paths(self, ws):
        pj = f"/api/workspaces/{ws.id}/projects/{self.proj_b.id}"
        iss = f"{pj}/issues/{self.issue_b.id}"
        return [
            f"{pj}/", f"{pj}/issues/", f"{iss}/", f"{iss}/comments/", f"{iss}/comments/{self.comment_b.id}/",
            f"{iss}/attachments/", f"{iss}/attachments/{self.att_b.id}/download/",
            f"{pj}/reports/", f"{pj}/reports/{self.report_b.id}/", f"{pj}/reports/export/issues/",
            f"/api/workspaces/{ws.id}/webhooks/{self.hook_b.id}/",
            f"/api/workspaces/{ws.id}/webhooks/{self.hook_b.id}/deliveries/",
            f"/api/workspaces/{ws.id}/notifications/{self.note_b.id}/read/",
            f"/api/workspaces/{ws.id}/audit/", f"/api/workspaces/{ws.id}/members/",
        ]

    def test_reads_are_denied_and_leak_nothing(self):
        # Under B's workspace URL every path 404s because A's owner is not a member of B.
        # Under A's workspace URL, B's project/issue/etc. ids simply do not exist for A (404),
        # except the list endpoints that are scoped to A's own (empty) data.
        for ws, strict in ((self.ws_b, True), (self.ws_a, False)):
            for path in self._paths(ws):
                method = self.client.post if path.endswith("/read/") else self.client.get
                r = method(path)
                body = r.content.decode() if not r.streaming else b"".join(r.streaming_content).decode()
                self.assertNotIn("confidential", body, path)
                self.assertNotIn("whsec_", body, path)
                if strict:
                    self.assertEqual(r.status_code, 404, path)
                else:
                    self.assertIn(r.status_code, (200, 404), path)
        # B-id-bearing paths under A's workspace must be 404 specifically
        for path in self._paths(self.ws_a):
            if str(self.proj_b.id) in path or str(self.hook_b.id) in path or str(self.note_b.id) in path:
                method = self.client.post if path.endswith("/read/") else self.client.get
                self.assertEqual(method(path).status_code, 404, path)

    def test_writes_are_denied_and_change_nothing(self):
        for ws in (self.ws_a, self.ws_b):
            pj = f"/api/workspaces/{ws.id}/projects/{self.proj_b.id}"
            iss = f"{pj}/issues/{self.issue_b.id}"
            for method, path, body in (
                    ("post", f"{iss}/comments/", {"body": "injected"}),
                    ("patch", f"{iss}/comments/{self.comment_b.id}/", {"body": "injected"}),
                    ("delete", f"{iss}/comments/{self.comment_b.id}/", None),
                    ("delete", f"{iss}/attachments/{self.att_b.id}/", None),
                    ("post", f"{pj}/reports/", {}),
                    ("patch", f"/api/workspaces/{ws.id}/webhooks/{self.hook_b.id}/", {"active": False}),
                    ("delete", f"/api/workspaces/{ws.id}/webhooks/{self.hook_b.id}/", None),
            ):
                r = getattr(self.client, method)(path, body, format="json") if body is not None else getattr(self.client, method)(path)
                self.assertIn(r.status_code, (403, 404), (method, path))
        self.comment_b.refresh_from_db()
        self.assertEqual(self.comment_b.body, "confidential-comment")
        self.assertTrue(Attachment.objects.filter(pk=self.att_b.pk).exists())
        self.assertTrue(WebhookEndpoint.objects.filter(pk=self.hook_b.pk, active=True).exists())
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Comment.objects.count(), 1)


class SearchAndFilterIsolationTests(BaseAPITest):
    def test_search_and_filters_only_see_own_tenant(self):
        ws_a, ua = make_tenant("A", "oa@a.test")
        ws_b, ub = make_tenant("B", "ob@b.test")
        proj_a = make_project(ws_a, ua["owner"], "AAA")
        proj_b = make_project(ws_b, ub["owner"], "BBB")
        make_issue(proj_a, ua["owner"], "ordinary task")
        make_issue(proj_b, ub["owner"], "confidential roadmap", priority="urgent")
        self.client.force_authenticate(ua["owner"])
        base = f"/api/workspaces/{ws_a.id}/projects/{proj_a.id}/issues/"
        for params in ({"q": "confidential"}, {"priority": "urgent"}, {"label": "x"}, {"ordering": "title"}):
            body = self.client.get(base, params).json()
            self.assertNotIn("confidential", json.dumps(body), params)
        self.assertEqual(self.client.get(base, {"q": "confidential"}).json()["count"], 0)
        # same query aimed at tenant B's project is refused outright
        foreign = f"/api/workspaces/{ws_a.id}/projects/{proj_b.id}/issues/"
        self.assertEqual(self.client.get(foreign, {"q": "confidential"}).status_code, 404)

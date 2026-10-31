from audit.models import AuditEvent
from issues.tests import IssueBase
from tenancy.testing import make_issue, make_project, make_tenant, purl

from .models import Comment


class CommentTests(IssueBase):
    def setUp(self):
        super().setUp()
        self.issue = make_issue(self.project, self.owner)
        self.curl = purl(self.ws, self.project, f"issues/{self.issue.id}/comments/")

    def test_create_list_and_validation(self):
        self.client.force_authenticate(self.member)
        r = self.client.post(self.curl, {"body": "  Looks good  "}, format="json")
        self.assertEqual((r.status_code, r.json()["body"], r.json()["author_email"]), (201, "Looks good", "m@a.test"))
        self.assertEqual(self.client.post(self.curl, {"body": "   "}, format="json").status_code, 400)
        self.assertEqual(self.client.get(self.curl).json()["count"], 1)

    def test_only_author_can_edit_and_edit_is_marked(self):
        c = Comment.objects.create(workspace=self.ws, project=self.project, issue=self.issue,
                                   author=self.member, body="mine")
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(f"{self.curl}{c.id}/", {"body": "x"}, format="json").status_code, 403)
        self.client.force_authenticate(self.member)
        r = self.client.patch(f"{self.curl}{c.id}/", {"body": "edited"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.json()["edited_at"])

    def test_delete_rules(self):
        c = Comment.objects.create(workspace=self.ws, project=self.project, issue=self.issue,
                                   author=self.owner, body="owner's")
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.delete(f"{self.curl}{c.id}/").status_code, 403)
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.delete(f"{self.curl}{c.id}/").status_code, 204)
        self.assertTrue(AuditEvent.objects.filter(event_type="comment.deleted_by_moderator").exists())

    def test_foreign_issue_id_is_404(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        foreign = make_issue(make_project(ws_b, ub["owner"], "BEE"), ub["owner"])
        self.client.force_authenticate(self.owner)
        r = self.client.post(purl(self.ws, self.project, f"issues/{foreign.id}/comments/"), {"body": "x"}, format="json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)

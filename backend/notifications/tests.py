import uuid

from django.core import mail

from issues.tests import IssueBase
from projects.models import ProjectMember
from tenancy.testing import make_issue, make_project, make_tenant, purl

from .models import Notification
from .tasks import notify_event


class NotificationFlowTests(IssueBase):
    def test_assignment_creates_in_app_and_email_notification_for_assignee_only(self):
        self.client.force_authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(self.url, {"title": "Fix", "assignee": self.member.id}, format="json")
        self.assertEqual(r.status_code, 201)
        n = Notification.objects.get()
        self.assertEqual((n.recipient, n.event_type), (self.member, "issue.assigned"))
        self.assertEqual(mail.outbox[-1].to, ["m@a.test"])

    def test_status_change_notifies_reporter_and_assignee_but_not_actor(self):
        issue = make_issue(self.project, self.owner, assignee=self.member)  # reporter = owner
        self.client.force_authenticate(self.pm)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(f"{self.url}{issue.id}/move/", {"status": str(self.st["In Progress"].id)}, format="json")
        self.assertEqual({n.recipient for n in Notification.objects.all()}, {self.owner, self.member})

    def test_task_is_idempotent_per_event(self):
        issue = make_issue(self.project, self.owner, assignee=self.member)
        args = (str(uuid.uuid4()), "comment.created", str(self.ws.id), str(issue.id), self.pm.id, {})
        notify_event(*args)
        notify_event(*args)
        self.assertEqual(Notification.objects.filter(recipient=self.member).count(), 1)

    def test_task_with_wrong_workspace_creates_nothing(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        issue = make_issue(self.project, self.owner, assignee=self.member)
        notify_event(str(uuid.uuid4()), "comment.created", str(ws_b.id), str(issue.id), ub["owner"].id, {})
        self.assertEqual(Notification.objects.count(), 0)

    def test_recipient_without_project_access_is_skipped(self):
        issue = make_issue(self.project, self.owner, assignee=self.member)
        ProjectMember.objects.filter(project=self.project, user=self.member).delete()
        notify_event(str(uuid.uuid4()), "comment.created", str(self.ws.id), str(issue.id), self.pm.id, {})
        self.assertFalse(Notification.objects.filter(recipient=self.member).exists())


class NotificationApiTests(IssueBase):
    def setUp(self):
        super().setUp()
        issue = make_issue(self.project, self.owner)
        self.n_member = Notification.objects.create(workspace=self.ws, recipient=self.member, event_type="x",
                                                    message="for member", issue=issue, dedupe_key="1")
        self.n_pm = Notification.objects.create(workspace=self.ws, recipient=self.pm, event_type="x",
                                                message="for pm", dedupe_key="2")
        self.base = f"/api/workspaces/{self.ws.id}/notifications/"

    def test_users_only_see_their_own(self):
        self.client.force_authenticate(self.member)
        msgs = [n["message"] for n in self.client.get(self.base).json()["results"]]
        self.assertEqual(msgs, ["for member"])
        self.assertEqual(self.client.post(f"{self.base}{self.n_pm.id}/read/").status_code, 404)

    def test_mark_read_and_read_all(self):
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(f"{self.base}{self.n_member.id}/read/").status_code, 200)
        self.assertEqual(self.client.get(self.base, {"unread": "true"}).json()["count"], 0)
        self.client.force_authenticate(self.pm)
        self.assertEqual(self.client.post(self.base + "read-all/").json(), {"marked_read": 1})

    def test_foreign_workspace_is_404(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        self.client.force_authenticate(ub["owner"])
        self.assertEqual(self.client.get(self.base).status_code, 404)

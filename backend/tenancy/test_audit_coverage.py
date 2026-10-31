"""The brief lists the event categories the audit log must capture. This drives the real API and checks
that each category produces a record (with actor and workspace) and that secrets never appear in metadata."""
import json
from unittest import mock

from audit.models import AuditEvent
from issues.tests import IssueBase
from tenancy.testing import PW, make_pro, make_user
from workspaces.models import Membership

REQUIRED = {
    "auth.login", "auth.login_failed", "workspace.created", "workspace.updated", "invitation.created",
    "membership.role_changed", "membership.removed", "project.created", "project.updated", "issue.created",
    "issue.status_changed", "workflow.status_created", "workflow.transition_created", "webhook.created",
    "sprint.created", "sprint.started",
}


class AuditCoverageTests(IssueBase):
    def test_every_required_category_is_recorded(self):
        make_pro(self.ws)
        c = self.client
        # authentication events
        c.post("/api/auth/login/", {"email": "o@a.test", "password": PW}, format="json")
        c.post("/api/auth/login/", {"email": "o@a.test", "password": "bad"}, format="json")
        c.force_authenticate(self.owner)
        base = f"/api/workspaces/{self.ws.id}"
        # workspace / membership / role
        c.patch(f"{base}/", {"name": "Renamed"}, format="json")
        c.post(f"{base}/invitations/", {"email": "new@x.test", "role": "member"}, format="json")
        mid = Membership.objects.get(workspace=self.ws, user=self.member).id
        c.patch(f"{base}/members/{mid}/", {"role": "project_manager"}, format="json")
        extra = make_user("extra@a.test")
        em = Membership.objects.create(workspace=self.ws, user=extra, role="member")
        c.delete(f"{base}/members/{em.id}/")
        # project / workflow / issues / sprints
        c.post(f"{base}/projects/", {"name": "Second", "key": "SEC"}, format="json")
        c.patch(f"{base}/projects/{self.project.id}/", {"description": "d"}, format="json")
        pb = f"{base}/projects/{self.project.id}"
        s = c.post(f"{pb}/statuses/", {"name": "Review", "category": "in_progress", "position": 3}, format="json").json()
        c.post(f"{pb}/transitions/", {"from_status": str(self.st["To Do"].id), "to_status": s["id"]}, format="json")
        issue = c.post(f"{pb}/issues/", {"title": "Audit me"}, format="json").json()
        c.post(f"{pb}/issues/{issue['id']}/move/", {"status": str(self.st["In Progress"].id)}, format="json")
        sp = c.post(f"{pb}/sprints/", {"name": "S", "start_date": "2026-11-02", "end_date": "2026-11-09"}, format="json").json()
        c.post(f"{pb}/sprints/{sp['id']}/start/")
        # webhooks
        with mock.patch("webhooks.security.resolve_host", return_value=["93.184.216.34"]):
            c.post(f"{base}/webhooks/", {"url": "https://h.example.com/x", "events": ["*"]}, format="json")

        seen = set(AuditEvent.objects.values_list("event_type", flat=True))
        self.assertEqual(REQUIRED - seen, set(), "missing audit categories")
        # every workspace-scoped event names the actor and workspace
        for ev in AuditEvent.objects.filter(event_type__in=["project.created", "issue.created", "webhook.created"]):
            self.assertIsNotNone(ev.actor_id)
            self.assertEqual(ev.workspace_id, self.ws.id)
        # no secrets in stored metadata
        blob = json.dumps(list(AuditEvent.objects.values_list("metadata", flat=True)))
        for forbidden in ("whsec_", PW, "password", "token"):
            self.assertNotIn(forbidden, blob)

    def test_platform_admin_login_is_audited(self):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_platform_admin("root@p.test", PW)
        self.client.post("/api/platform-admin/login/", {"email": "root@p.test", "password": PW}, format="json")
        self.assertTrue(AuditEvent.objects.filter(event_type="platform_admin.login").exists())

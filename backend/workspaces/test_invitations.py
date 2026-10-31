import re
from datetime import timedelta

from django.core import mail
from django.utils import timezone

from audit.models import AuditEvent
from tenancy.testing import BaseAPITest, make_pro, make_tenant, make_user

from .models import Invitation, Membership, Role


class InvitationTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", admin="ad@a.test", member="m@a.test")
        self.owner, self.admin, self.member = u["owner"], u["admin"], u["member"]
        make_pro(self.ws)  # Free allows only 3 members; this workspace already has 3
        self.url = f"/api/workspaces/{self.ws.id}/invitations/"

    def _invite(self, email="new@x.test", role="member"):
        self.client.force_authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {"email": email, "role": role}, format="json")

    def _token(self):
        return re.search(r"token=([^\s]+)", mail.outbox[-1].body).group(1)

    def test_invite_sends_email_without_leaking_token_in_api(self):
        r = self._invite()
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("token", r.json())
        self.assertEqual(mail.outbox[-1].to, ["new@x.test"])

    def test_cannot_invite_as_owner_and_member_cannot_invite(self):
        self.assertEqual(self._invite(role="owner").status_code, 400)
        self.client.force_authenticate(self.member)
        r = self.client.post(self.url, {"email": "z@x.test", "role": "member"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_accept_flow_adds_membership_with_invited_role_and_audits(self):
        self._invite("new@x.test", "project_manager")
        token = self._token()
        invitee = make_user("new@x.test")
        self.client.force_authenticate(invitee)
        r = self.client.post("/api/invitations/accept/", {"token": token}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Membership.objects.get(user=invitee, workspace=self.ws).role, Role.PROJECT_MANAGER)
        self.assertTrue(AuditEvent.objects.filter(event_type="invitation.accepted").exists())
        again = self.client.post("/api/invitations/accept/", {"token": token}, format="json")
        self.assertEqual(again.status_code, 400)

    def test_accept_rejected_for_other_email_expired_and_revoked(self):
        self._invite("new@x.test")
        token = self._token()
        self.client.force_authenticate(make_user("other@x.test"))
        self.assertEqual(self.client.post("/api/invitations/accept/", {"token": token}, format="json").status_code, 400)

        inv = Invitation.objects.get()
        invitee = make_user("new@x.test")
        self.client.force_authenticate(invitee)
        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.post("/api/invitations/accept/", {"token": token}, format="json").status_code, 400)

        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() + timedelta(days=1),
                                                    revoked_at=timezone.now())
        self.assertEqual(self.client.post("/api/invitations/accept/", {"token": token}, format="json").status_code, 400)
        self.assertFalse(Membership.objects.filter(user=invitee, workspace=self.ws).exists())

    def test_tampered_token_rejected(self):
        self.client.force_authenticate(make_user("new@x.test"))
        r = self.client.post("/api/invitations/accept/", {"token": "garbage"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_revoke_invitation(self):
        self._invite()
        inv = Invitation.objects.get()
        r = self.client.delete(f"{self.url}{inv.pk}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.client.get(self.url).json()["results"], [])


class MemberManagementTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", admin="ad@a.test", member="m@a.test",
                                 project_manager="pm@a.test")
        self.owner, self.admin = u["owner"], u["admin"]
        self.member, self.pm = u["member"], u["project_manager"]
        self.m = {k: Membership.objects.get(workspace=self.ws, user=v) for k, v in u.items()}

    def url(self, key):
        return f"/api/workspaces/{self.ws.id}/members/{self.m[key].id}/"

    def test_admin_can_change_member_but_not_grant_admin_or_touch_owner(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(self.url("member"), {"role": "project_manager"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.url("member"), {"role": "admin"}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(self.url("owner"), {"role": "member"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.url("owner")).status_code, 403)

    def test_member_and_pm_cannot_manage_members(self):
        for user in (self.member, self.pm):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.patch(self.url("pm"), {"role": "admin"}, format="json").status_code, 403)

    def test_last_owner_is_protected(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(self.url("owner"), {"role": "admin"}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(self.url("owner")).status_code, 400)

    def test_owner_can_remove_member_and_it_is_audited(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(self.url("member")).status_code, 204)
        self.assertTrue(AuditEvent.objects.filter(event_type="membership.removed", workspace=self.ws).exists())

    def test_cannot_manage_member_of_another_workspace(self):
        ws_b, ub = make_tenant("B", "ob@b.test", member="mb@b.test")
        target = Membership.objects.get(workspace=ws_b, user=ub["member"])
        self.client.force_authenticate(self.owner)
        r = self.client.delete(f"/api/workspaces/{self.ws.id}/members/{target.id}/")
        self.assertEqual(r.status_code, 404)  # not in the caller's workspace scope
        self.assertTrue(Membership.objects.filter(pk=target.pk).exists())


class AuditLogTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws_a, ua = make_tenant("A", "oa@a.test", member="ma@a.test")
        self.ws_b, ub = make_tenant("B", "ob@b.test")
        self.owner_a, self.member_a, self.owner_b = ua["owner"], ua["member"], ub["owner"]

    def test_audit_visible_to_owner_only_own_events_and_denied_to_member(self):
        self.client.force_authenticate(self.owner_a)
        self.client.patch(f"/api/workspaces/{self.ws_a.id}/", {"name": "A2"}, format="json")
        self.client.force_authenticate(self.owner_b)
        self.client.patch(f"/api/workspaces/{self.ws_b.id}/", {"name": "B2"}, format="json")

        self.client.force_authenticate(self.owner_a)
        events = self.client.get(f"/api/workspaces/{self.ws_a.id}/audit/").json()["results"]
        self.assertTrue(events)
        self.assertTrue(all(e["resource_id"] == str(self.ws_a.id) for e in events))

        self.client.force_authenticate(self.member_a)
        self.assertEqual(self.client.get(f"/api/workspaces/{self.ws_a.id}/audit/").status_code, 403)

    def test_audit_events_are_immutable(self):
        ev = AuditEvent.objects.create(event_type="x")
        with self.assertRaises(PermissionError):
            ev.event_type = "y"
            ev.save()
        with self.assertRaises(PermissionError):
            ev.delete()

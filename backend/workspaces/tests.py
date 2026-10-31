from django.db import IntegrityError, transaction

from tenancy.testing import PW, BaseAPITest, make_tenant, make_user
from django.contrib.auth import get_user_model

from .models import Membership, Role

User = get_user_model()


class TenantIsolationTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws_a, ua = make_tenant("A", "oa@a.test", member="ma@a.test")
        self.ws_b, ub = make_tenant("B", "ob@b.test")
        self.owner_a, self.member_a, self.owner_b = ua["owner"], ua["member"], ub["owner"]

    def test_list_only_returns_own_workspaces(self):
        self.client.force_authenticate(self.owner_a)
        data = self.client.get("/api/workspaces/").json()
        self.assertEqual([w["name"] for w in data["results"]], ["A"])

    def test_cross_tenant_retrieve_update_are_404(self):
        self.client.force_authenticate(self.owner_a)
        url = f"/api/workspaces/{self.ws_b.id}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"name": "x"}, format="json").status_code, 404)
        self.ws_b.refresh_from_db()
        self.assertEqual(self.ws_b.name, "B")

    def test_cross_tenant_nested_endpoints_are_404_for_owner(self):
        self.client.force_authenticate(self.owner_a)
        w = self.ws_b.id
        for path in (f"members/", f"invitations/", f"audit/"):
            r = self.client.get(f"/api/workspaces/{w}/{path}")
            self.assertEqual(r.status_code, 404, path)
            self.assertNotIn("ob@b.test", r.content.decode())
        r = self.client.post(f"/api/workspaces/{w}/invitations/",
                             {"email": "x@x.test", "role": "member"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_members_list_scoped_to_own_workspace(self):
        self.client.force_authenticate(self.member_a)
        emails = {m["email"] for m in
                  self.client.get(f"/api/workspaces/{self.ws_a.id}/members/").json()["results"]}
        self.assertEqual(emails, {"oa@a.test", "ma@a.test"})

    def test_unauthenticated_is_rejected(self):
        self.assertIn(self.client.get("/api/workspaces/").status_code, (401, 403))


class RoleTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", member="m@a.test")
        self.owner, self.member = u["owner"], u["member"]

    def test_member_cannot_edit_workspace(self):
        self.client.force_authenticate(self.member)
        r = self.client.patch(f"/api/workspaces/{self.ws.id}/", {"name": "x"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_owner_can_edit_workspace(self):
        self.client.force_authenticate(self.owner)
        r = self.client.patch(f"/api/workspaces/{self.ws.id}/", {"name": "Renamed"}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_creator_becomes_owner_and_cannot_choose_role(self):
        user = make_user("new@x.test")
        self.client.force_authenticate(user)
        r = self.client.post("/api/workspaces/", {"name": "New Co", "role": "member"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Membership.objects.get(user=user).role, Role.OWNER)


class PlatformAdminModelTests(BaseAPITest):
    def test_only_one_active_platform_admin_at_db_level(self):
        User.objects.create_platform_admin("a@p.test", PW)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_platform_admin("b@p.test", PW)

    def test_create_user_ignores_is_platform_admin(self):
        u = User.objects.create_user("u@x.test", PW, is_platform_admin=True)
        self.assertFalse(u.is_platform_admin)

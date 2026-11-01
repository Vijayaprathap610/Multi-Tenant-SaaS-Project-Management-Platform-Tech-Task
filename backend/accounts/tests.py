import re

from django.contrib.auth import get_user_model
from django.core import mail

from audit.models import AuditEvent
from tenancy.testing import PW, BaseAPITest, make_user

User = get_user_model()


class RegistrationTests(BaseAPITest):
    def test_register_creates_ordinary_user(self):
        r = self.client.post("/api/auth/register/", {"email": "New@X.test", "password": PW,
                                                     "is_platform_admin": True}, format="json")
        self.assertEqual(r.status_code, 201)
        u = User.objects.get(email="new@x.test")
        self.assertFalse(u.is_platform_admin)
        self.assertFalse(u.memberships.exists())  # no automatic workspace access

    def test_duplicate_registration_looks_identical(self):
        make_user("dup@x.test")
        r1 = self.client.post("/api/auth/register/", {"email": "dup@x.test", "password": PW}, format="json")
        r2 = self.client.post("/api/auth/register/", {"email": "fresh@x.test", "password": PW}, format="json")
        self.assertEqual((r1.status_code, r1.json()), (r2.status_code, r2.json()))
        self.assertEqual(User.objects.filter(email="dup@x.test").count(), 1)

    def test_weak_password_rejected(self):
        r = self.client.post("/api/auth/register/", {"email": "a@x.test", "password": "123"}, format="json")
        self.assertEqual(r.status_code, 400)


class LoginTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.user = make_user("u@x.test")
        self.admin = User.objects.create_platform_admin("root@p.test", PW)

    def test_login_logout_me(self):
        r = self.client.post("/api/auth/login/", {"email": "U@x.test", "password": PW}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertIn(self.client.get("/api/auth/me/").status_code, (401, 403))

    def test_failure_message_identical_for_unknown_and_wrong_password(self):
        a = self.client.post("/api/auth/login/", {"email": "u@x.test", "password": "bad"}, format="json")
        b = self.client.post("/api/auth/login/", {"email": "none@x.test", "password": "bad"}, format="json")
        self.assertEqual((a.status_code, a.json()), (b.status_code, b.json()))

    def test_platform_admin_cannot_use_ordinary_login_and_vice_versa(self):
        r = self.client.post("/api/auth/login/", {"email": "root@p.test", "password": PW}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/platform-admin/login/", {"email": "u@x.test", "password": PW}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_platform_admin_login_and_stats(self):
        r = self.client.post("/api/platform-admin/login/", {"email": "root@p.test", "password": PW}, format="json")
        self.assertEqual(r.status_code, 200)
        stats = self.client.get("/api/platform-admin/stats/")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(
    set(stats.json()),
    {"total_users", "total_workspaces", "total_memberships", "subscriptions"},
)

    def test_ordinary_user_cannot_read_platform_stats(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/platform-admin/stats/").status_code, 403)

    def test_login_is_rate_limited(self):
        codes = [self.client.post("/api/auth/login/", {"email": "u@x.test", "password": "bad"},
                                  format="json").status_code for _ in range(12)]
        self.assertIn(429, codes)

    def test_login_events_are_audited(self):
        self.client.post("/api/auth/login/", {"email": "u@x.test", "password": PW}, format="json")
        self.client.post("/api/auth/login/", {"email": "u@x.test", "password": "bad"}, format="json")
        types = set(AuditEvent.objects.values_list("event_type", flat=True))
        self.assertTrue({"auth.login", "auth.login_failed"} <= types)


class PasswordResetTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.user = make_user("r@x.test")

    def _request_link(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post("/api/auth/password-reset/", {"email": "r@x.test"}, format="json")
        self.assertEqual(r.status_code, 202)
        m = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[-1].body)
        return m.group(1), m.group(2)

    def test_reset_flow_is_single_use(self):
        uid, token = self._request_link()
        new = "An0ther-Str0ng-pw!"
        ok = self.client.post("/api/auth/password-reset/confirm/",
                              {"uid": uid, "token": token, "new_password": new}, format="json")
        self.assertEqual(ok.status_code, 200)
        again = self.client.post("/api/auth/password-reset/confirm/",
                                 {"uid": uid, "token": token, "new_password": "Yet-An0ther-pw!9"}, format="json")
        self.assertEqual(again.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new))

    def test_unknown_email_gives_same_response_and_sends_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post("/api/auth/password-reset/", {"email": "ghost@x.test"}, format="json")
        self.assertEqual(r.status_code, 202)
        self.assertEqual(len(mail.outbox), 0)

    def test_bad_token_rejected(self):
        uid, _ = self._request_link()
        r = self.client.post("/api/auth/password-reset/confirm/",
                             {"uid": uid, "token": "nope", "new_password": "Str0ng-new-pw!1"}, format="json")
        self.assertEqual(r.status_code, 400)


class ProfileTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.user = make_user("p@x.test")
        self.client.force_authenticate(self.user)

    def test_update_name_only_not_email_or_privileges(self):
        r = self.client.patch("/api/auth/me/", {"first_name": "Pat", "email": "evil@x.test",
                                                "is_platform_admin": True}, format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.email, self.user.is_platform_admin), ("Pat", "p@x.test", False))

    def test_change_password_requires_current_and_validates(self):
        bad = self.client.post("/api/auth/change-password/", {"current_password": "nope", "new_password": "Brand-New-pw-91!"}, format="json")
        self.assertEqual(bad.status_code, 400)
        weak = self.client.post("/api/auth/change-password/", {"current_password": PW, "new_password": "123"}, format="json")
        self.assertEqual(weak.status_code, 400)
        ok = self.client.post("/api/auth/change-password/", {"current_password": PW, "new_password": "Brand-New-pw-91!"}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-New-pw-91!"))


class PlatformAdminCommandTests(BaseAPITest):
    def _run(self, email="Root@P.test", password=PW):
        import os
        from io import StringIO
        from unittest import mock

        from django.core.management import call_command
        with mock.patch.dict(os.environ, {"PLATFORM_ADMIN_PASSWORD": password}):
            call_command("create_platform_admin", email=email, stdout=StringIO())

    def test_creates_the_admin_with_hashed_password_and_no_staff_flag(self):
        self._run()
        u = User.objects.get(is_platform_admin=True)
        self.assertEqual(u.email, "root@p.test")
        self.assertTrue(u.check_password(PW))
        self.assertNotEqual(u.password, PW)
        self.assertFalse(u.is_staff)

    def test_refuses_to_create_a_second_active_admin(self):
        from django.core.management.base import CommandError
        self._run()
        with self.assertRaises(CommandError):
            self._run(email="second@p.test")
        self.assertEqual(User.objects.filter(is_platform_admin=True).count(), 1)

    def test_weak_password_is_rejected(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self._run(password="123")
        self.assertFalse(User.objects.filter(is_platform_admin=True).exists())

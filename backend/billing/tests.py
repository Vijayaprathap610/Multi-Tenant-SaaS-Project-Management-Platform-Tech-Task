from types import SimpleNamespace
from unittest import mock

from django.test import override_settings

from audit.models import AuditEvent
from issues.tests import IssueBase
from tenancy.testing import BaseAPITest, make_pro, make_tenant, purl
from workspaces.models import Invitation

from .models import StripeEvent, Subscription
from .plans import PLANS
from .services import InvalidWebhook, effective_plan

STRIPE = dict(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_t",
              STRIPE_PRICE_PRO="price_pro", STRIPE_PRICE_BUSINESS="price_biz")


def stripe_sub(sub_id="sub_1", customer="cus_1", status="active", price="price_pro", cancel=False):
    return {"id": sub_id, "customer": customer, "status": status, "cancel_at_period_end": cancel,
            "current_period_end": 1893456000, "items": {"data": [{"price": {"id": price}}]}}


def event(eid, kind, obj):
    return {"id": eid, "type": kind, "data": {"object": obj}}


@override_settings(**STRIPE)
class BillingApiTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", admin="ad@a.test", member="m@a.test")
        self.owner, self.admin, self.member = u["owner"], u["admin"], u["member"]
        self.base = f"/api/workspaces/{self.ws.id}/billing/"

    def test_status_shows_free_plan_limits_and_usage(self):
        self.client.force_authenticate(self.admin)
        body = self.client.get(self.base).json()
        self.assertEqual((body["plan"], body["limits"]["projects"], body["usage"]["members"], body["can_manage"]),
                         ("free", 2, 3, False))
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get(self.base).status_code, 403)

    def test_only_owner_can_start_checkout_cancel_or_open_portal(self):
        self.client.force_authenticate(self.admin)
        for path in ("checkout/", "portal/", "cancel/"):
            self.assertEqual(self.client.post(self.base + path, {"plan": "pro"}, format="json").status_code, 403)

    def test_owner_checkout_creates_customer_and_session(self):
        fake = mock.MagicMock()
        fake.Customer.create.return_value = SimpleNamespace(id="cus_1")
        fake.checkout.Session.create.return_value = SimpleNamespace(url="https://checkout.stripe.test/s")
        self.client.force_authenticate(self.owner)
        with mock.patch("billing.views.get_stripe", return_value=fake):
            r = self.client.post(self.base + "checkout/", {"plan": "pro"}, format="json")
        self.assertEqual((r.status_code, r.json()["url"]), (200, "https://checkout.stripe.test/s"))
        kwargs = fake.checkout.Session.create.call_args.kwargs
        self.assertEqual((kwargs["mode"], kwargs["client_reference_id"]), ("subscription", str(self.ws.id)))
        self.assertEqual(kwargs["line_items"][0]["price"], "price_pro")
        self.assertEqual(Subscription.objects.get().stripe_customer_id, "cus_1")
        # still Free until Stripe confirms payment
        self.assertEqual(effective_plan(self.ws), "free")

    def test_unknown_plan_rejected(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(self.base + "checkout/", {"plan": "enterprise"}, format="json").status_code, 400)

    def test_cannot_start_second_checkout_when_subscribed(self):
        Subscription.objects.create(workspace=self.ws, plan="pro", status="active", stripe_customer_id="cus_1",
                                    stripe_subscription_id="sub_1")
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(self.base + "checkout/", {"plan": "business"}, format="json").status_code, 400)

    def test_cancel_marks_cancel_at_period_end(self):
        Subscription.objects.create(workspace=self.ws, plan="pro", status="active", stripe_customer_id="cus_1",
                                    stripe_subscription_id="sub_1")
        fake = mock.MagicMock()
        self.client.force_authenticate(self.owner)
        with mock.patch("billing.views.get_stripe", return_value=fake):
            r = self.client.post(self.base + "cancel/")
        self.assertEqual(r.status_code, 200)
        fake.Subscription.modify.assert_called_once_with("sub_1", cancel_at_period_end=True)
        self.assertTrue(Subscription.objects.get().cancel_at_period_end)

    def test_other_tenants_billing_is_404(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(f"/api/workspaces/{ws_b.id}/billing/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/workspaces/{ws_b.id}/billing/portal/").status_code, 404)


@override_settings(**STRIPE)
class StripeWebhookTests(BaseAPITest):
    URL = "/api/billing/webhook/"

    def setUp(self):
        super().setUp()
        self.ws, _ = make_tenant("A", "o@a.test")
        self.sub = Subscription.objects.create(workspace=self.ws, stripe_customer_id="cus_1")

    def _post(self, ev):
        with mock.patch("billing.views.construct_event", return_value=ev):
            return self.client.post(self.URL, data=b"{}", content_type="application/json",
                                    HTTP_STRIPE_SIGNATURE="t=1,v1=x")

    def test_bad_signature_rejected_and_nothing_changes(self):
        with mock.patch("billing.views.construct_event", side_effect=InvalidWebhook()):
            r = self.client.post(self.URL, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="bad")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(StripeEvent.objects.count(), 0)

    def test_real_signature_verification_path_rejects_unsigned_payload(self):
        r = self.client.post(self.URL, data=b'{"id":"evt_x"}', content_type="application/json")
        self.assertEqual(r.status_code, 400)  # no mocks: construct_event itself must refuse

    def test_subscription_updated_upgrades_plan_and_is_audited(self):
        r = self._post(event("evt_1", "customer.subscription.updated", stripe_sub()))
        self.assertEqual(r.json(), {"status": "ok"})
        self.sub.refresh_from_db()
        self.assertEqual((self.sub.plan, self.sub.status, self.sub.stripe_subscription_id), ("pro", "active", "sub_1"))
        self.assertIsNotNone(self.sub.current_period_end)
        self.assertEqual(effective_plan(self.ws), "pro")
        self.assertTrue(AuditEvent.objects.filter(event_type="billing.subscription_updated", workspace=self.ws).exists())

    def test_duplicate_event_is_processed_once(self):
        ev = event("evt_dup", "customer.subscription.updated", stripe_sub())
        self.assertEqual(self._post(ev).json(), {"status": "ok"})
        self.assertEqual(self._post(ev).json(), {"status": "duplicate"})
        self.assertEqual(AuditEvent.objects.filter(event_type="billing.subscription_updated").count(), 1)

    def test_deleted_or_unpaid_subscription_falls_back_to_free(self):
        self._post(event("evt_a", "customer.subscription.updated", stripe_sub()))
        self.assertEqual(effective_plan(self.ws), "pro")
        self._post(event("evt_b", "customer.subscription.deleted", stripe_sub(status="canceled")))
        self.assertEqual(effective_plan(self.ws), "free")

    def test_past_due_keeps_access_during_retry_window(self):
        self._post(event("evt_c", "customer.subscription.updated", stripe_sub(status="past_due")))
        self.assertEqual(effective_plan(self.ws), "pro")

    def test_unknown_customer_is_ignored(self):
        r = self._post(event("evt_x", "customer.subscription.updated", stripe_sub(sub_id="sub_zzz", customer="cus_other")))
        self.assertEqual(r.status_code, 200)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan, "free")

    def test_checkout_completed_links_subscription_only_for_matching_customer(self):
        fake = mock.MagicMock()
        fake.Subscription.retrieve.return_value = stripe_sub(status="trialing", price="price_biz")
        obj = {"client_reference_id": str(self.ws.id), "customer": "cus_1", "subscription": "sub_1"}
        with mock.patch("billing.services.get_stripe", return_value=fake):
            self._post(event("evt_co", "checkout.session.completed", obj))
        self.sub.refresh_from_db()
        self.assertEqual((self.sub.plan, self.sub.status), ("business", "trialing"))
        # a forged customer id for the same workspace does nothing
        self.sub.plan, self.sub.status, self.sub.stripe_subscription_id = "free", "inactive", ""
        self.sub.save()
        with mock.patch("billing.services.get_stripe", return_value=fake):
            self._post(event("evt_co2", "checkout.session.completed", {**obj, "customer": "cus_evil"}))
        self.sub.refresh_from_db()
        self.assertEqual((self.sub.plan, self.sub.stripe_subscription_id), ("free", ""))


class PlanLimitTests(IssueBase):
    def test_project_limit_enforced_then_lifted_by_upgrade(self):
        self.client.force_authenticate(self.owner)
        base = f"/api/workspaces/{self.ws.id}/projects/"
        # IssueBase already created one project (PRJ); Free allows 2
        self.assertEqual(self.client.post(base, {"name": "Two", "key": "TWO"}, format="json").status_code, 201)
        r = self.client.post(base, {"name": "Three", "key": "THR"}, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual((r.json()["code"], r.json()["resource"]), ("plan_limit", "projects"))
        make_pro(self.ws)
        self.assertEqual(self.client.post(base, {"name": "Three", "key": "THR"}, format="json").status_code, 201)

    def test_member_limit_counts_pending_invitations(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post(f"/api/workspaces/{self.ws.id}/invitations/", {"email": "x@x.test", "role": "member"}, format="json")
        self.assertEqual((r.status_code, r.json()["resource"]), (403, "members"))
        self.assertEqual(Invitation.objects.count(), 0)

    def test_storage_limit(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from tenancy.testing import make_issue
        issue = make_issue(self.project, self.owner)
        self.client.force_authenticate(self.owner)
        url = purl(self.ws, self.project, f"issues/{issue.id}/attachments/")
        with mock.patch.dict(PLANS["free"], {"storage_mb": 0}):
            r = self.client.post(url, {"file": SimpleUploadedFile("a.txt", b"hello")}, format="multipart")
        self.assertEqual((r.status_code, r.json()["resource"]), (403, "storage"))

    def test_webhook_limit(self):
        from webhooks.models import WebhookEndpoint
        WebhookEndpoint.objects.create(workspace=self.ws, url="https://a.example.com/h", events=["*"], secret="s")
        self.client.force_authenticate(self.owner)
        with mock.patch("webhooks.security.resolve_host", return_value=["93.184.216.34"]):
            r = self.client.post(f"/api/workspaces/{self.ws.id}/webhooks/",
                                 {"url": "https://b.example.com/h", "events": ["*"]}, format="json")
        self.assertEqual((r.status_code, r.json()["resource"]), (403, "webhooks"))

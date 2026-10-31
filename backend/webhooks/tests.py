import hashlib
import hmac
import json
import uuid
from datetime import timedelta
from unittest import mock

from django.utils import timezone

from issues.tests import IssueBase
from tenancy.testing import make_tenant

from .models import DeliveryStatus, WebhookDelivery, WebhookEndpoint
from .tasks import MAX_ATTEMPTS, dispatch_event, prune_deliveries

PUBLIC = ["93.184.216.34"]
URL = "https://hooks.example.com/techtask"


class WebhookBase(IssueBase):
    def setUp(self):
        super().setUp()
        p = mock.patch("webhooks.security.resolve_host", return_value=PUBLIC)
        p.start()
        self.addCleanup(p.stop)
        self.base = f"/api/workspaces/{self.ws.id}/webhooks/"

    def _create(self, user=None, **over):
        self.client.force_authenticate(user or self.owner)
        body = {"url": URL, "events": ["issue.created"], **over}
        return self.client.post(self.base, body, format="json")

    def _new_issue(self):
        self.client.force_authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {"title": "Hooked"}, format="json")


class EndpointManagementTests(WebhookBase):
    def test_secret_shown_once_and_never_listed(self):
        r = self._create()
        self.assertEqual(r.status_code, 201)
        secret = r.json()["secret"]
        self.assertTrue(secret.startswith("whsec_"))
        ep_id = r.json()["id"]
        for resp in (self.client.get(self.base), self.client.get(f"{self.base}{ep_id}/"),
                     self.client.get(f"{self.base}{ep_id}/deliveries/")):
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(secret, resp.content.decode())
            self.assertNotIn("secret", resp.content.decode())

    def test_rotate_returns_new_secret(self):
        r = self._create()
        old = r.json()["secret"]
        new = self.client.post(f"{self.base}{r.json()['id']}/rotate-secret/").json()["secret"]
        self.assertNotEqual(old, new)
        self.assertEqual(WebhookEndpoint.objects.get().secret, new)

    def test_only_owner_and_admin_can_manage(self):
        self.assertEqual(self._create(self.pm).status_code, 403)
        self.assertEqual(self._create(self.member).status_code, 403)

    def test_invalid_event_http_and_private_targets_rejected(self):
        self.assertEqual(self._create(events=["nope"]).status_code, 400)
        self.assertEqual(self._create(url="http://hooks.example.com/x").status_code, 400)
        with mock.patch("webhooks.security.resolve_host", return_value=["10.0.0.5"]):
            self.assertEqual(self._create().status_code, 400)
        with mock.patch("webhooks.security.resolve_host", return_value=["127.0.0.1"]):
            self.assertEqual(self._create().status_code, 400)
        self.assertEqual(WebhookEndpoint.objects.count(), 0)


class DeliveryTests(WebhookBase):
    def test_signed_delivery_on_event(self):
        secret = self._create().json()["secret"]
        with mock.patch("webhooks.delivery.http_post", return_value=200) as post:
            self._new_issue()
        self.assertEqual(post.call_count, 1)
        url, body, headers, _ = post.call_args[0]
        self.assertEqual(url, URL)
        ts, sig = (p.split("=", 1)[1] for p in headers["X-TechTask-Signature"].split(","))
        expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        self.assertTrue(hmac.compare_digest(sig, expected))
        payload = json.loads(body)
        self.assertEqual((payload["type"], payload["data"]["key"]), ("issue.created", "PRJ-1"))
        self.assertEqual(payload["workspace_id"], str(self.ws.id))
        d = WebhookDelivery.objects.get()
        self.assertEqual((d.status, d.attempts, d.response_status), (DeliveryStatus.SUCCESS, 1, 200))
        self.assertEqual(headers["X-TechTask-Delivery"], str(d.pk))

    def test_unsubscribed_events_are_not_delivered(self):
        self._create(events=["comment.created"])
        with mock.patch("webhooks.delivery.http_post", return_value=200) as post:
            self._new_issue()
        self.assertEqual(post.call_count, 0)
        self.assertEqual(WebhookDelivery.objects.count(), 0)

    def test_failing_endpoint_is_retried_then_marked_failed(self):
        self._create()
        with mock.patch("webhooks.delivery.http_post", return_value=500) as post:
            self._new_issue()
        d = WebhookDelivery.objects.get()
        self.assertEqual((d.status, d.attempts, d.error), (DeliveryStatus.FAILED, MAX_ATTEMPTS, "HTTP 500"))
        self.assertEqual(post.call_count, MAX_ATTEMPTS)

    def test_retry_can_recover(self):
        self._create()
        with mock.patch("webhooks.delivery.http_post", side_effect=[500, 502, 204]):
            self._new_issue()
        d = WebhookDelivery.objects.get()
        self.assertEqual((d.status, d.attempts), (DeliveryStatus.SUCCESS, 3))

    def test_timeouts_are_recorded_by_class_name_only(self):
        self._create()
        with mock.patch("webhooks.delivery.http_post", side_effect=TimeoutError("secret detail")):
            self._new_issue()
        d = WebhookDelivery.objects.get()
        self.assertEqual(d.error, "TimeoutError")
        self.assertNotIn("secret detail", d.error)

    def test_duplicate_dispatch_creates_one_delivery(self):
        self._create()
        eid = str(uuid.uuid4())
        with mock.patch("webhooks.delivery.http_post", return_value=200) as post:
            dispatch_event(eid, "issue.created", str(self.ws.id), {"key": "X"})
            dispatch_event(eid, "issue.created", str(self.ws.id), {"key": "X"})
        self.assertEqual(WebhookDelivery.objects.count(), 1)
        self.assertEqual(post.call_count, 1)

    def test_events_never_reach_another_tenants_endpoint(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        ep_b = WebhookEndpoint.objects.create(workspace=ws_b, url="https://b.example.com/h",
                                              events=["*"], secret="whsec_b")
        self._create()
        with mock.patch("webhooks.delivery.http_post", return_value=200) as post:
            self._new_issue()
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args[0][0], URL)
        self.assertFalse(WebhookDelivery.objects.filter(endpoint=ep_b).exists())

    def test_target_is_revalidated_at_delivery_time(self):
        self._create()
        with mock.patch("webhooks.security.resolve_host", return_value=["10.1.2.3"]), \
                mock.patch("webhooks.delivery.http_post", return_value=200) as post:
            self._new_issue()
        self.assertEqual(post.call_count, 0)
        d = WebhookDelivery.objects.get()
        self.assertEqual((d.status, d.error), (DeliveryStatus.FAILED, "UnsafeTarget"))

    def test_ping_action_and_pruning(self):
        ep_id = self._create().json()["id"]
        with mock.patch("webhooks.delivery.http_post", return_value=200), self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(f"{self.base}{ep_id}/test/")
        self.assertEqual(r.status_code, 202)
        d = WebhookDelivery.objects.get()
        self.assertEqual((d.event_type, d.status), ("ping", DeliveryStatus.SUCCESS))
        WebhookDelivery.objects.update(created_at=timezone.now() - timedelta(days=40))
        self.assertEqual(prune_deliveries(), 1)

    def test_cross_tenant_endpoint_ids_are_404(self):
        ws_b, ub = make_tenant("B", "ob@b.test")
        ep_b = WebhookEndpoint.objects.create(workspace=ws_b, url="https://b.example.com/h",
                                              events=["*"], secret="whsec_b")
        self.client.force_authenticate(self.owner)
        for method, path in (("get", ""), ("patch", ""), ("delete", ""), ("get", "deliveries/"),
                             ("post", "rotate-secret/"), ("post", "test/")):
            r = getattr(self.client, method)(f"{self.base}{ep_b.id}/{path}")
            self.assertEqual(r.status_code, 404, (method, path))
        ep_b.refresh_from_db()
        self.assertEqual(ep_b.secret, "whsec_b")

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from django.utils import timezone

from .security import UnsafeTarget, validate_target_url

TIMEOUT_SECONDS = 10


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a 3xx is treated as a failure, never followed


def http_post(url, body, headers, timeout=TIMEOUT_SECONDS):
    """Returns the HTTP status code; network errors propagate. Separate function so tests can replace it."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def sign(secret, timestamp, body):
    mac = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256)
    return f"t={timestamp},v1={mac.hexdigest()}"


def build_body(delivery):
    return json.dumps({"id": str(delivery.event_id), "type": delivery.event_type,
                       "workspace_id": str(delivery.workspace_id),
                       "created_at": delivery.created_at.isoformat(), "data": delivery.payload},
                      sort_keys=True, separators=(",", ":")).encode()


def attempt(delivery):
    """One delivery attempt. Returns (ok, http_status_or_None, short_error)."""
    endpoint = delivery.endpoint
    if endpoint.workspace_id != delivery.workspace_id:  # defensive tenant check
        return False, None, "TenantMismatch"
    try:
        validate_target_url(endpoint.url)
    except UnsafeTarget:
        return False, None, "UnsafeTarget"
    body = build_body(delivery)
    ts = int(time.time())
    headers = {"Content-Type": "application/json", "User-Agent": "TechTask-Webhooks/1.0",
               "X-TechTask-Event": delivery.event_type, "X-TechTask-Delivery": str(delivery.pk),
               "X-TechTask-Signature": sign(endpoint.secret, ts, body)}
    try:
        status = http_post(endpoint.url, body, headers, TIMEOUT_SECONDS)
    except Exception as exc:  # timeouts, DNS, TLS ... only the class name is stored
        return False, None, type(exc).__name__
    if 200 <= status < 300:
        return True, status, ""
    return False, status, f"HTTP {status}"


def mark_delivered(delivery):
    delivery.delivered_at = timezone.now()

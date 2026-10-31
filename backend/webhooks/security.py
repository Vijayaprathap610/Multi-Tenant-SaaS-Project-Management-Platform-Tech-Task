import ipaddress
import socket
from urllib.parse import urlparse

from django.conf import settings


class UnsafeTarget(ValueError):
    pass


def resolve_host(host):
    return sorted({ai[4][0] for ai in socket.getaddrinfo(host, None)})


def validate_target_url(url):
    """SSRF guard, run when an endpoint is saved AND again at delivery time (DNS can change)."""
    parts = urlparse(url)
    allowed = {"https"} | ({"http"} if settings.WEBHOOK_ALLOW_HTTP else set())
    if parts.scheme not in allowed:
        raise UnsafeTarget("Webhook URLs must use https.")
    if not parts.hostname or parts.username or parts.password:
        raise UnsafeTarget("Invalid webhook URL.")
    try:
        addresses = resolve_host(parts.hostname)
    except OSError:
        raise UnsafeTarget("The webhook host could not be resolved.")
    if not settings.WEBHOOK_ALLOW_PRIVATE_NETWORKS:
        for addr in addresses:
            ip = ipaddress.ip_address(addr)
            if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                    or ip.is_multicast or ip.is_unspecified):
                raise UnsafeTarget("Webhook URLs may not point to private or internal addresses.")

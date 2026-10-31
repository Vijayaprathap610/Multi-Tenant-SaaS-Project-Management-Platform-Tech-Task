from django.conf import settings

# None = unlimited. Limits are enforced on the backend (billing.services.enforce_limit).
PLANS = {
    "free": {"name": "Free", "members": 3, "projects": 2, "storage_mb": 50, "webhooks": 1},
    "pro": {"name": "Pro", "members": 15, "projects": 20, "storage_mb": 1024, "webhooks": 10},
    "business": {"name": "Business", "members": None, "projects": None, "storage_mb": 10240, "webhooks": 50},
}


def price_id(plan):
    return {"pro": settings.STRIPE_PRICE_PRO, "business": settings.STRIPE_PRICE_BUSINESS}.get(plan, "")


def plan_for_price(pid):
    for key in ("pro", "business"):
        if pid and price_id(key) == pid:
            return key
    return None

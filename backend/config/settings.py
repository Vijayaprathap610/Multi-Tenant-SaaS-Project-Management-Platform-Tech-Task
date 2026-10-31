import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
# Fails loudly if missing: no default secret, ever.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "tenancy",
    "audit",
    "workspaces",
    "projects",
    "workflows",
    "boards",
    "sprints",
    "issues",
    "comments",
    "attachments",
    "notifications",
    "webhooks",
    "reports",
    "billing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["POSTGRES_DB"],
    "USER": os.environ["POSTGRES_USER"],
    "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"django.contrib.auth.password_validation.{n}"}
    for n in ("UserAttributeSimilarityValidator", "MinimumLengthValidator",
              "CommonPasswordValidator", "NumericPasswordValidator")
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
USE_TZ = True
TIME_ZONE = "UTC"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "tenancy.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min", "user": "600/min",
        "login": "10/min", "register": "10/min",
        "password_reset": "5/min", "platform_login": "5/min",
    },
}

# The SPA and the API share one origin (Vite proxy in development, nginx in production), so no CORS headers are
# sent: browsers therefore refuse every cross-origin request (an allow-list of "same origin only").
# These origins are only trusted for CSRF checks, e.g. the dev server on http://localhost:5173.
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("TRUSTED_ORIGINS", "").split(",") if o]

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_ACKS_LATE = True

if not DEBUG:
    # Only valid behind a trusted proxy that sets X-Forwarded-Proto (see docs/deployment.md).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Email / links
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Tech Task <no-reply@techtask.local>")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
PASSWORD_RESET_TIMEOUT = 3600  # seconds; reset tokens are also single-use (password hash is part of the token)

# Run Celery tasks inline under `manage.py test`
if "test" in sys.argv:
    CELERY_TASK_ALWAYS_EAGER = True
    # Fast hasher for the test run only (never used outside `manage.py test`).
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    # The test client speaks plain HTTP: never redirect to https or require Secure cookies there,
    # even when DJANGO_DEBUG is unset (the production defaults above would otherwise redirect every request).
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Private file storage (never served by a static/media URL; downloads go through an authorized view)
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
ATTACHMENT_MAX_BYTES = int(os.environ.get("ATTACHMENT_MAX_BYTES", 10 * 1024 * 1024))
# Optional malware scanner, e.g. "clamdscan --no-summary". Empty = no scanning. Fails closed.
ATTACHMENT_SCAN_COMMAND = os.environ.get("ATTACHMENT_SCAN_COMMAND", "")

NOTIFY_BY_EMAIL = os.environ.get("NOTIFY_BY_EMAIL", "true").lower() == "true"

# Webhooks: refuse private/loopback targets (SSRF) unless explicitly allowed for local development
WEBHOOK_ALLOW_PRIVATE_NETWORKS = os.environ.get("WEBHOOK_ALLOW_PRIVATE_NETWORKS", "false").lower() == "true"
WEBHOOK_ALLOW_HTTP = os.environ.get("WEBHOOK_ALLOW_HTTP", "false").lower() == "true"

from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "prune-webhook-deliveries": {"task": "webhooks.tasks.prune_deliveries", "schedule": crontab(hour=3, minute=0)},
    "prune-notifications": {"task": "notifications.tasks.prune_notifications", "schedule": crontab(hour=3, minute=15)},
    "prune-invitations": {"task": "workspaces.tasks.prune_invitations", "schedule": crontab(hour=3, minute=30)},
}

# Stripe (test mode only). Secret key stays on the backend; never exposed to the frontend.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_BUSINESS = os.environ.get("STRIPE_PRICE_BUSINESS", "")

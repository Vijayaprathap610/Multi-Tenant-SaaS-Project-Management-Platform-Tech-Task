from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from audit.services import record

from .permissions import IsPlatformAdmin
from .serializers import (ChangePasswordSerializer, EmailSerializer, LoginSerializer, MeSerializer,
                          PasswordResetConfirmSerializer, RegisterSerializer)
from .tasks import send_password_reset_email

User = get_user_model()


class PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(PublicView):
    throttle_classes = []

    def get(self, request):
        return Response({"detail": "CSRF cookie set."})


class RegisterView(PublicView):
    throttle_scope = "register"

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        # Same response whether or not the address already exists (no account enumeration).
        if not User.objects.filter(email__iexact=d["email"]).exists():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(d["email"], d["password"],
                                                    first_name=d.get("first_name", ""),
                                                    last_name=d.get("last_name", ""))
                record("auth.registered", actor=user)
            except IntegrityError:
                pass
        return Response({"detail": "Registration received. You can now sign in."},
                        status=status.HTTP_201_CREATED)


def _credential_login(request, *, platform_admin):
    s = LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)

    user = authenticate(
        request,
        username=s.validated_data["email"].strip().lower(),
        password=s.validated_data["password"],
    )

    if user is None:
        record(
            "platform_admin.login_failed"
            if platform_admin
            else "auth.login_failed"
        )
        return None

    # Strict separation between ordinary users and platform admins.
    if user.is_platform_admin != platform_admin:
        record(
            "platform_admin.login_failed"
            if platform_admin
            else "auth.login_failed",
            actor=user,
        )
        return None

    login(request, user)

    record(
        "platform_admin.login" if platform_admin else "auth.login",
        actor=user,
    )

    return user


class LoginView(PublicView):
    throttle_scope = "login"

    def post(self, request):
        user = _credential_login(request, platform_admin=False)
        if user is None:
            return Response({"detail": "Invalid email or password."}, status=400)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        record("auth.logout", actor=request.user)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        if request.user.is_platform_admin:
            return Response({"id": request.user.id, "email": request.user.email, "is_platform_admin": True, "memberships": []})
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        if request.user.is_platform_admin:
            return Response({"detail": "Not found."}, status=404)
        updates = []
        if "first_name" in request.data:
            request.user.first_name = str(request.data["first_name"])[:150]
            updates.append("first_name")
        if "last_name" in request.data:
            request.user.last_name = str(request.data["last_name"])[:150]
            updates.append("last_name")
        if "designation" in request.data:
            request.user.designation = str(request.data["designation"])[:100]
            updates.append("designation")
        if "contact_number" in request.data:
            request.user.contact_number = str(request.data["contact_number"])[:30]
            updates.append("contact_number")
        if updates:
            request.user.save(update_fields=updates)
        return Response(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(s.validated_data["current_password"]):
            return Response({"current_password": ["Current password is incorrect."]}, status=400)
        try:
            validate_password(s.validated_data["new_password"], user=user)
        except DjangoValidationError as exc:
            return Response({"new_password": exc.messages}, status=400)
        user.set_password(s.validated_data["new_password"])
        user.save(update_fields=["password"])
        update_session_auth_hash(request, user)  # keep this session, invalidate all others
        record("auth.password_changed", actor=user)
        return Response({"detail": "Password updated."})


class PasswordResetRequestView(PublicView):
    throttle_scope = "password_reset"

    def post(self, request):
        s = EmailSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=s.validated_data["email"], is_active=True,
                                   is_platform_admin=False).first()
        if user:
            transaction.on_commit(lambda: send_password_reset_email.delay(user.pk))
        return Response({"detail": "If that address has an account, a reset email is on its way."},
                        status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(PublicView):
    throttle_scope = "password_reset"

    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        bad = Response({"detail": "Invalid or expired reset link."}, status=400)
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(d["uid"])),
                                    is_active=True, is_platform_admin=False)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return bad
        if not default_token_generator.check_token(user, d["token"]):
            return bad
        try:
            validate_password(d["new_password"], user=user)
        except DjangoValidationError as exc:
            return Response({"new_password": exc.messages}, status=400)
        user.set_password(d["new_password"])  # also invalidates the token and other sessions
        user.save(update_fields=["password"])
        record("auth.password_reset", actor=user)
        return Response({"detail": "Password updated."})


class PlatformAdminLoginView(PublicView):
    throttle_scope = "platform_login"

    def post(self, request):
        user = _credential_login(request, platform_admin=True)
        if user is None:
            return Response({"detail": "Invalid email or password."}, status=400)
        return Response({"email": user.email, "is_platform_admin": True})


class PlatformAdminStatsView(APIView):
    """Aggregates only; never returns tenant content."""
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from billing.models import Subscription
        from django.db.models import Count
        from workspaces.models import Membership, Workspace
        return Response({
            "total_users": User.objects.filter(is_platform_admin=False).count(),
            "total_workspaces": Workspace.objects.count(),
            "total_memberships": Membership.objects.count(),
            "subscriptions": [{"plan": r["plan"], "status": r["status"], "count": r["n"]} for r in
                              Subscription.objects.values("plan", "status").annotate(n=Count("id"))],
        })


class PlatformAdminAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        import datetime
        from billing.models import Subscription
        from django.conf import settings as django_settings
        from django.utils import timezone
        from issues.models import Issue
        from projects.models import Project
        from workspaces.models import Membership, Workspace

        now = timezone.now()
        thirty_days_ago = now - datetime.timedelta(days=30)

        plan_counts = {"free": 0, "pro": 0, "business": 0}
        for sub in Subscription.objects.all():
            p = sub.plan.lower()
            if p in plan_counts:
                plan_counts[p] += 1
        total_workspaces = Workspace.objects.count()
        workspaces_with_sub = Subscription.objects.count()
        plan_counts["free"] += max(0, total_workspaces - workspaces_with_sub)

        return Response({
            "total_users": User.objects.filter(is_platform_admin=False).count(),
            "active_users": User.objects.filter(is_platform_admin=False, is_active=True).count(),
            "total_workspaces": total_workspaces,
            "total_memberships": Membership.objects.count(),
            "total_projects": Project.objects.count(),
            "active_projects": Project.objects.filter(status="active").count(),
            "total_issues": Issue.objects.count(),
            "recent_users_30d": User.objects.filter(is_platform_admin=False, date_joined__gte=thirty_days_ago).count(),
            "recent_workspaces_30d": Workspace.objects.filter(created_at__gte=thirty_days_ago).count(),
            "plan_distribution": plan_counts,
            "system_health": {
                "status": "operational",
                "database": "connected",
                "timestamp": now.isoformat(),
            },
        })


class PlatformAdminCompaniesView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from billing.models import Subscription
        from django.db.models import Count, Q
        from issues.models import Issue
        from projects.models import Project
        from workspaces.models import Membership, Role, Workspace

        q = request.query_params.get("q", "").strip()
        plan_filter = request.query_params.get("plan", "").strip().lower()

        qs = Workspace.objects.all().order_by("-created_at")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(created_by__email__icontains=q))

        project_counts = dict(Project.objects.values("workspace_id").annotate(c=Count("id")).values_list("workspace_id", "c"))
        issue_counts = dict(Issue.objects.values("workspace_id").annotate(c=Count("id")).values_list("workspace_id", "c"))
        member_counts = dict(Membership.objects.values("workspace_id").annotate(c=Count("id")).values_list("workspace_id", "c"))
        subscriptions = {s.workspace_id: s for s in Subscription.objects.all()}

        owner_memberships = {
            m.workspace_id: m.user
            for m in Membership.objects.filter(role=Role.OWNER).select_related("user")
        }

        results = []
        for ws in qs:
            sub = subscriptions.get(ws.id)
            plan = sub.plan if sub else "free"
            sub_status = sub.status if sub else "active"
            if plan_filter and plan != plan_filter:
                continue

            owner = owner_memberships.get(ws.id) or ws.created_by
            owner_info = None
            if owner:
                owner_info = {
                    "id": owner.id,
                    "email": owner.email,
                    "name": f"{owner.first_name} {owner.last_name}".strip() or owner.email,
                }

            results.append({
                "id": str(ws.id),
                "name": ws.name,
                "slug": ws.slug,
                "created_at": ws.created_at.isoformat(),
                "owner": owner_info,
                "members_count": member_counts.get(ws.id, 0),
                "projects_count": project_counts.get(ws.id, 0),
                "issues_count": issue_counts.get(ws.id, 0),
                "plan": plan,
                "subscription_status": sub_status,
                "is_active": True,
            })

        return Response(results)


class PlatformAdminCompanyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request, workspace_id):
        from billing.models import Subscription
        from billing.plans import PLANS
        from django.shortcuts import get_object_or_404
        from issues.models import Issue
        from projects.models import Project
        from workspaces.models import Membership, Role, Workspace

        ws = get_object_or_404(Workspace, id=workspace_id)
        sub = Subscription.objects.filter(workspace=ws).first()
        plan = sub.plan if sub else "free"
        limits = PLANS.get(plan, {})

        members = []
        for m in Membership.objects.filter(workspace=ws).select_related("user").order_by("created_at"):
            members.append({
                "id": str(m.id),
                "user_id": m.user.id,
                "email": m.user.email,
                "name": f"{m.user.first_name} {m.user.last_name}".strip() or m.user.email,
                "role": m.role,
                "designation": m.designation,
                "contact_number": m.contact_number,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat(),
            })

        projects = []
        for p in Project.objects.filter(workspace=ws).order_by("-created_at"):
            projects.append({
                "id": str(p.id),
                "name": p.name,
                "key": p.key,
                "status": p.status,
                "issues_count": Issue.objects.filter(project=p).count(),
                "created_at": p.created_at.isoformat(),
            })

        owner_member = Membership.objects.filter(workspace=ws, role=Role.OWNER).select_related("user").first()
        owner = owner_member.user if owner_member else ws.created_by

        return Response({
            "workspace": {
                "id": str(ws.id),
                "name": ws.name,
                "slug": ws.slug,
                "created_at": ws.created_at.isoformat(),
            },
            "owner": {
                "id": owner.id,
                "email": owner.email,
                "name": f"{owner.first_name} {owner.last_name}".strip() or owner.email,
            } if owner else None,
            "subscription": {
                "plan": plan,
                "status": sub.status if sub else "active",
                "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
                "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
                "stripe_customer_id": sub.stripe_customer_id if sub else "",
                "stripe_subscription_id": sub.stripe_subscription_id if sub else "",
            },
            "limits": limits,
            "members": members,
            "projects": projects,
            "total_issues": Issue.objects.filter(workspace=ws).count(),
        })

    def patch(self, request, workspace_id):
        import datetime
        from billing.models import Subscription
        from billing.plans import PLANS
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        from workspaces.models import Workspace

        ws = get_object_or_404(Workspace, id=workspace_id)
        data = request.data

        if "name" in data and str(data["name"]).strip():
            ws.name = str(data["name"]).strip()[:120]
            ws.save(update_fields=["name"])

        if "plan" in data:
            new_plan = str(data["plan"]).strip().lower()
            if new_plan in PLANS:
                sub, _ = Subscription.objects.get_or_create(workspace=ws)
                sub.plan = new_plan
                sub.status = "active"
                if not sub.current_period_end:
                    sub.current_period_end = timezone.now() + datetime.timedelta(days=365)
                sub.save()
                record("platform_admin.plan_override", actor=request.user, workspace=ws, metadata={"new_plan": new_plan})

        return Response({"detail": "Company updated successfully."})


class PlatformAdminSubscriptionsView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from billing.models import Subscription
        from workspaces.models import Membership, Role, Workspace

        subs = {s.workspace_id: s for s in Subscription.objects.all()}
        owners = {
            m.workspace_id: m.user.email
            for m in Membership.objects.filter(role=Role.OWNER).select_related("user")
        }

        results = []
        for ws in Workspace.objects.all().order_by("-created_at"):
            sub = subs.get(ws.id)
            plan = sub.plan if sub else "free"
            status_val = sub.status if sub else "active"
            owner_email = owners.get(ws.id) or (ws.created_by.email if ws.created_by else "")
            results.append({
                "workspace_id": str(ws.id),
                "workspace_name": ws.name,
                "workspace_slug": ws.slug,
                "owner_email": owner_email,
                "plan": plan,
                "status": status_val,
                "stripe_customer_id": sub.stripe_customer_id if sub else "",
                "stripe_subscription_id": sub.stripe_subscription_id if sub else "",
                "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
                "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
                "updated_at": (sub.updated_at if sub else ws.created_at).isoformat(),
            })

        return Response(results)


class PlatformAdminSubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def patch(self, request, workspace_id):
        import datetime
        from billing.models import Subscription
        from billing.plans import PLANS
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        from workspaces.models import Workspace

        ws = get_object_or_404(Workspace, id=workspace_id)
        data = request.data
        sub, _ = Subscription.objects.get_or_create(workspace=ws)

        if "plan" in data:
            plan = str(data["plan"]).strip().lower()
            if plan in PLANS:
                sub.plan = plan
                sub.status = "active"
                if not sub.current_period_end:
                    sub.current_period_end = timezone.now() + datetime.timedelta(days=365)
        if "status" in data:
            sub.status = str(data["status"]).strip()

        sub.save()
        record("platform_admin.subscription_updated", actor=request.user, workspace=ws, metadata=data)
        return Response({"detail": "Subscription updated."})


class PlatformAdminUsersView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from django.db.models import Q

        q = request.query_params.get("q", "").strip()
        active_filter = request.query_params.get("active", "").strip().lower()

        qs = User.objects.filter(is_platform_admin=False).prefetch_related("memberships__workspace").order_by("-date_joined")
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
        if active_filter in ("true", "false"):
            qs = qs.filter(is_active=(active_filter == "true"))

        results = []
        for u in qs:
            workspaces = []
            for m in u.memberships.all():
                workspaces.append({
                    "id": str(m.workspace.id),
                    "name": m.workspace.name,
                    "role": m.role,
                    "is_active": m.is_active,
                })
            results.append({
                "id": u.id,
                "email": u.email,
                "name": f"{u.first_name} {u.last_name}".strip() or u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "designation": getattr(u, "designation", ""),
                "contact_number": getattr(u, "contact_number", ""),
                "is_active": u.is_active,
                "date_joined": u.date_joined.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "workspaces": workspaces,
            })

        return Response(results)


class PlatformAdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def patch(self, request, user_id):
        from django.shortcuts import get_object_or_404
        u = get_object_or_404(User, id=user_id, is_platform_admin=False)
        data = request.data
        updates = []

        if "is_active" in data:
            u.is_active = bool(data["is_active"])
            updates.append("is_active")
        if "first_name" in data:
            u.first_name = str(data["first_name"])[:150]
            updates.append("first_name")
        if "last_name" in data:
            u.last_name = str(data["last_name"])[:150]
            updates.append("last_name")
        if "designation" in data:
            u.designation = str(data["designation"])[:100]
            updates.append("designation")
        if "contact_number" in data:
            u.contact_number = str(data["contact_number"])[:30]
            updates.append("contact_number")

        if updates:
            u.save(update_fields=updates)
            record("platform_admin.user_updated", actor=request.user, resource=u, metadata=data)

        return Response({"detail": "User updated."})


class PlatformAdminActivityView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from audit.models import AuditEvent

        events = AuditEvent.objects.select_related("actor", "workspace").order_by("-created_at")[:100]
        results = []
        for e in events:
            results.append({
                "id": e.id,
                "event_type": e.event_type,
                "actor_email": e.actor.email if e.actor else "System",
                "workspace_name": e.workspace.name if e.workspace else "Platform",
                "workspace_id": str(e.workspace.id) if e.workspace else None,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "metadata": e.metadata,
                "created_at": e.created_at.isoformat(),
            })
        return Response(results)


DEFAULT_PLATFORM_SETTINGS = {
    "allow_registration": True,
    "maintenance_mode": False,
    "system_banner": "",
    "demo_payment_gateway": True,
    "default_free_members": 3,
    "default_free_projects": 2,
    "support_email": "admin@techtask.local",
    "enforce_strong_passwords": True,
}


def _settings_path():
    import os
    from django.conf import settings as django_settings
    base = getattr(django_settings, "BASE_DIR", None)
    if base:
        return os.path.join(str(base), "platform_settings.json")
    return "platform_settings.json"


def _load_settings():
    import json
    p = _settings_path()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_PLATFORM_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_PLATFORM_SETTINGS.copy()


def _save_settings(data):
    import json
    p = _settings_path()
    current = _load_settings()
    current.update(data)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception:
        pass
    return current


class PlatformAdminSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        return Response(_load_settings())

    def post(self, request):
        updated = _save_settings(request.data)
        record("platform_admin.settings_changed", actor=request.user, metadata=request.data)
        return Response(updated)

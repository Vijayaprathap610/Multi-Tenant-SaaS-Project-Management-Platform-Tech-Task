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

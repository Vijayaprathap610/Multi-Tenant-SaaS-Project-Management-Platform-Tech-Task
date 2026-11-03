import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import DestroyAPIView, GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import record
from billing.services import enforce_limit
from projects.models import Project, ProjectMember
from tenancy.mixins import TenantScopedMixin

from .invites import resolve
from .models import ALL_ROLES, MANAGE_ROLES, Invitation, Membership, Role, Workspace
from .serializers import (AcceptInvitationSerializer, CreateMemberSerializer, InvitationSerializer,
                          MemberSerializer, MemberUpdateSerializer, RoleChangeSerializer, WorkspaceSerializer)
from .tasks import send_invitation_email, send_member_welcome_email

User = get_user_model()
PM_UP = MANAGE_ROLES | {Role.PROJECT_MANAGER.value}


class CanEditWorkspace(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.my_role in MANAGE_ROLES


class WorkspaceViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    """Only workspaces the caller belongs to are ever visible (404 otherwise)."""
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated, CanEditWorkspace]

    def get_queryset(self):
        role = Membership.objects.filter(workspace=OuterRef("pk"), user=self.request.user)
        return (Workspace.objects.filter(memberships__user=self.request.user)
                .annotate(my_role=Subquery(role.values("role")[:1])).order_by("name"))

    def perform_create(self, serializer):
        ws = serializer.save()
        record("workspace.created", actor=self.request.user, workspace=ws, resource=ws)

    def perform_update(self, serializer):
        ws = serializer.save()
        record("workspace.updated", actor=self.request.user, workspace=ws, resource=ws,
               metadata={"fields": sorted(serializer.validated_data)})


class MemberListView(TenantScopedMixin, ListCreateAPIView):
    serializer_class = MemberSerializer
    queryset = Membership.objects.select_related("user").order_by("created_at")
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        is_active = self.request.query_params.get("is_active")
        if is_active in ("true", "1"):
            qs = qs.filter(is_active=True)
        elif is_active in ("false", "0"):
            qs = qs.filter(is_active=False)
        return qs

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        s = CreateMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        ws = request.membership.workspace
        actor_role = request.membership.role
        target_role = d["role"]

        if actor_role == Role.PROJECT_MANAGER.value and target_role != Role.MEMBER.value:
            raise PermissionDenied("Project Managers can only create Team Members.")

        email = d["email"]
        if Membership.objects.filter(workspace=ws, user__email__iexact=email).exists():
            raise ValidationError({"email": "This person is already a member of this company."})

        full_name = d.get("full_name", "").strip()
        fn = d.get("first_name", "").strip()
        ln = d.get("last_name", "").strip()
        if full_name and not fn:
            parts = full_name.split(" ", 1)
            fn = parts[0]
            ln = parts[1] if len(parts) > 1 else ""

        designation = d.get("designation", "").strip()
        contact_number = d.get("contact_number", "").strip()
        password = d.get("password") or secrets.token_urlsafe(16)

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=fn,
                last_name=ln,
                designation=designation,
                contact_number=contact_number,
            )
        else:
            updates = []
            if fn and not user.first_name:
                user.first_name = fn
                updates.append("first_name")
            if ln and not user.last_name:
                user.last_name = ln
                updates.append("last_name")
            if designation and not user.designation:
                user.designation = designation
                updates.append("designation")
            if contact_number and not user.contact_number:
                user.contact_number = contact_number
                updates.append("contact_number")
            if updates:
                user.save(update_fields=updates)

        enforce_limit(ws, "members")

        membership = Membership.objects.create(
            workspace=ws,
            user=user,
            role=target_role,
            designation=designation,
            contact_number=contact_number,
            is_active=True,
        )

        project_id = d.get("project_id")
        if project_id:
            project = get_object_or_404(Project, pk=project_id, workspace=ws)
            if actor_role == Role.PROJECT_MANAGER.value:
                if not ProjectMember.objects.filter(project=project, user=request.user).exists():
                    raise PermissionDenied("You can only assign members to projects you belong to.")
            ProjectMember.objects.get_or_create(workspace=ws, project=project, user=user)

        record("membership.created", actor=request.user, workspace=ws, resource=membership,
               metadata={"role": target_role, "email": email, "designation": designation})

        transaction.on_commit(lambda: send_member_welcome_email.delay(str(membership.pk)))

        return Response(MemberSerializer(membership).data, status=status.HTTP_201_CREATED)


def _check_can_manage(actor, target, new_role=None):
    """Owners manage everyone. Admins manage only Project Managers and Members,
    and cannot grant Owner/Admin. Project Managers manage Members."""
    if actor.role == Role.OWNER:
        return
    if actor.role == Role.ADMIN:
        if target.role in (Role.OWNER, Role.ADMIN):
            raise PermissionDenied("Insufficient role to manage this member.")
        if new_role in (Role.OWNER, Role.ADMIN):
            raise PermissionDenied("Insufficient role to assign that role.")
        return
    if actor.role == Role.PROJECT_MANAGER:
        if target.role != Role.MEMBER:
            raise PermissionDenied("Project Managers can only manage Team Members.")
        if new_role and new_role != Role.MEMBER:
            raise PermissionDenied("Project Managers cannot change members to other roles.")
        return
    raise PermissionDenied("Insufficient privileges to manage members.")


def _guard_last_owner(target, losing_owner):
    if target.role == Role.OWNER and losing_owner:
        owners = Membership.objects.select_for_update().filter(
            workspace_id=target.workspace_id, role=Role.OWNER).count()
        if owners <= 1:
            raise ValidationError({"detail": "A workspace must keep at least one Owner."})


class MemberDetailView(TenantScopedMixin, GenericAPIView):
    queryset = Membership.objects.select_related("user", "workspace")
    serializer_class = MemberSerializer
    required_roles = {"PATCH": PM_UP, "DELETE": MANAGE_ROLES}

    @transaction.atomic
    def patch(self, request, **kwargs):
        target = get_object_or_404(self.get_queryset(), pk=kwargs["member_id"])
        s = MemberUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        new_role = d.get("role")
        if new_role is not None:
            _check_can_manage(request.membership, target, new_role)
            _guard_last_owner(target, losing_owner=new_role != Role.OWNER)
            old_role, target.role = target.role, new_role
            record("membership.role_changed", actor=request.user, workspace=target.workspace,
                   resource=target, metadata={"from": old_role, "to": new_role})

        if "designation" in d:
            target.designation = d["designation"]
        if "contact_number" in d:
            target.contact_number = d["contact_number"]
        if "is_active" in d:
            _check_can_manage(request.membership, target)
            if target.role == Role.OWNER and not d["is_active"]:
                raise ValidationError({"detail": "Cannot deactivate the workspace Owner."})
            target.is_active = d["is_active"]

        target.save()

        # Update user profile fields if provided
        user_updates = []
        if "first_name" in d:
            target.user.first_name = d["first_name"]
            user_updates.append("first_name")
        if "last_name" in d:
            target.user.last_name = d["last_name"]
            user_updates.append("last_name")
        if "designation" in d:
            target.user.designation = d["designation"]
            user_updates.append("designation")
        if "contact_number" in d:
            target.user.contact_number = d["contact_number"]
            user_updates.append("contact_number")
        if user_updates:
            target.user.save(update_fields=user_updates)

        # Update assigned projects if provided
        if "project_ids" in d:
            ws = target.workspace
            target_user = target.user
            if request.membership.role == Role.PROJECT_MANAGER:
                pm_projects = Project.objects.filter(workspace=ws, members__user=request.user)
                projects = pm_projects.filter(pk__in=d["project_ids"])
                ProjectMember.objects.filter(workspace=ws, user=target_user, project__in=pm_projects).exclude(project__in=projects).delete()
                for p in projects:
                    ProjectMember.objects.get_or_create(workspace=ws, project=p, user=target_user)
            else:
                projects = Project.objects.filter(workspace=ws, pk__in=d["project_ids"])
                ProjectMember.objects.filter(workspace=ws, user=target_user).exclude(project__in=projects).delete()
                for p in projects:
                    ProjectMember.objects.get_or_create(workspace=ws, project=p, user=target_user)

        # Handle direct password reset by Owner/Admin
        if d.get("new_password"):
            if request.membership.role not in MANAGE_ROLES:
                raise PermissionDenied("Only workspace owners and administrators can set employee passwords.")
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_password(d["new_password"], user=target.user)
            except DjangoValidationError as exc:
                raise ValidationError({"new_password": exc.messages})
            target.user.set_password(d["new_password"])
            target.user.save(update_fields=["password"])
            record("membership.password_reset", actor=request.user, workspace=target.workspace,
                   resource=target, metadata={"target_user_id": target.user_id})

        # Handle password reset email request by Owner/Admin
        if d.get("send_reset_email"):
            if request.membership.role not in MANAGE_ROLES:
                raise PermissionDenied("Only workspace owners and administrators can send password reset emails.")
            from accounts.tasks import send_password_reset_email
            target_uid = target.user_id
            transaction.on_commit(lambda: send_password_reset_email.delay(target_uid))
            record("membership.password_reset_email_sent", actor=request.user, workspace=target.workspace,
                   resource=target, metadata={"target_user_id": target.user_id})

        record("membership.updated", actor=request.user, workspace=target.workspace,
               resource=target, metadata={"is_active": target.is_active, "role": target.role})

        return Response(MemberSerializer(target).data)

    @transaction.atomic
    def delete(self, request, **kwargs):
        target = get_object_or_404(self.get_queryset(), pk=kwargs["member_id"])
        _check_can_manage(request.membership, target)
        _guard_last_owner(target, losing_owner=True)
        record("membership.removed", actor=request.user, workspace=target.workspace,
               resource=target, metadata={"role": target.role})
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationListCreateView(TenantScopedMixin, ListCreateAPIView):
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.filter(accepted_at__isnull=True,
                                         revoked_at__isnull=True).order_by("-created_at")
    required_roles = {"GET": MANAGE_ROLES, "POST": MANAGE_ROLES}

    @transaction.atomic
    def perform_create(self, serializer):
        ws = self.request.membership.workspace
        email = serializer.validated_data["email"]
        if Membership.objects.filter(workspace=ws, user__email__iexact=email).exists():
            raise ValidationError({"email": "This person is already a member."})
        if self.get_queryset().filter(email=email, expires_at__gt=timezone.now()).exists():
            raise ValidationError({"email": "A pending invitation already exists."})
        enforce_limit(ws, "members")  # members + pending invitations vs plan
        inv = serializer.save(workspace=ws, invited_by=self.request.user,
                              expires_at=timezone.now() + timedelta(days=7))
        record("invitation.created", actor=self.request.user, workspace=ws, resource=inv,
               metadata={"role": inv.role})
        transaction.on_commit(lambda: send_invitation_email.delay(str(inv.pk)))


class InvitationDetailView(TenantScopedMixin, DestroyAPIView):
    queryset = Invitation.objects.filter(accepted_at__isnull=True, revoked_at__isnull=True)
    required_roles = {"DELETE": MANAGE_ROLES}

    def perform_destroy(self, instance):
        instance.revoked_at = timezone.now()
        instance.save(update_fields=["revoked_at"])
        record("invitation.revoked", actor=self.request.user, workspace=instance.workspace,
               resource=instance)


class AcceptInvitationView(APIView):
    """The invitation is bound to one workspace, one role and one email address."""

    @transaction.atomic
    def post(self, request):
        s = AcceptInvitationSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        generic = Response({"detail": "Invalid or expired invitation."},
                           status=status.HTTP_400_BAD_REQUEST)
        inv = resolve(s.validated_data["token"])
        if inv is None or inv.email != request.user.email.lower():
            return generic
        inv = Invitation.objects.select_for_update().get(pk=inv.pk)
        if inv.accepted_at or inv.revoked_at:
            return generic
        if not Membership.objects.filter(workspace=inv.workspace, user=request.user).exists():
            enforce_limit(inv.workspace, "members", include_pending_invites=False)
        _, created = Membership.objects.get_or_create(
            workspace=inv.workspace, user=request.user, defaults={"role": inv.role})
        inv.accepted_at = timezone.now()
        inv.save(update_fields=["accepted_at"])
        record("invitation.accepted", actor=request.user, workspace=inv.workspace,
               resource=inv, metadata={"role": inv.role, "new_member": created})
        return Response({"workspace_id": str(inv.workspace_id)})

from datetime import timedelta

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
from tenancy.mixins import TenantScopedMixin

from .invites import resolve
from .models import ALL_ROLES, MANAGE_ROLES, Invitation, Membership, Role, Workspace
from .serializers import (AcceptInvitationSerializer, InvitationSerializer, MemberSerializer,
                          RoleChangeSerializer, WorkspaceSerializer)
from .tasks import send_invitation_email


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


class MemberListView(TenantScopedMixin, ListAPIView):
    serializer_class = MemberSerializer
    queryset = Membership.objects.select_related("user").order_by("created_at")
    required_roles = {"GET": ALL_ROLES}


def _check_can_manage(actor, target, new_role=None):
    """Owners manage everyone. Admins manage only Project Managers and Members,
    and cannot grant Owner/Admin."""
    if actor.role == Role.OWNER:
        return
    if target.role in (Role.OWNER, Role.ADMIN):
        raise PermissionDenied("Insufficient role to manage this member.")
    if new_role in (Role.OWNER, Role.ADMIN):
        raise PermissionDenied("Insufficient role to assign that role.")


def _guard_last_owner(target, losing_owner):
    if target.role == Role.OWNER and losing_owner:
        owners = Membership.objects.select_for_update().filter(
            workspace_id=target.workspace_id, role=Role.OWNER).count()
        if owners <= 1:
            raise ValidationError({"detail": "A workspace must keep at least one Owner."})


class MemberDetailView(TenantScopedMixin, GenericAPIView):
    queryset = Membership.objects.select_related("user", "workspace")
    serializer_class = MemberSerializer
    required_roles = {"PATCH": MANAGE_ROLES, "DELETE": MANAGE_ROLES}

    @transaction.atomic
    def patch(self, request, **kwargs):
        target = get_object_or_404(self.get_queryset(), pk=kwargs["member_id"])
        s = RoleChangeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        new_role = s.validated_data["role"]
        _check_can_manage(request.membership, target, new_role)
        _guard_last_owner(target, losing_owner=new_role != Role.OWNER)
        old_role, target.role = target.role, new_role
        target.save(update_fields=["role"])
        record("membership.role_changed", actor=request.user, workspace=target.workspace,
               resource=target, metadata={"from": old_role, "to": new_role})
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

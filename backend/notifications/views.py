from django.utils import timezone
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from tenancy.mixins import TenantScopedMixin
from workspaces.models import ALL_ROLES

from .models import Notification
from .serializers import NotificationSerializer


class _Own:
    """Notifications are personal: scoped to the workspace AND to the requesting user."""
    def get_queryset(self):
        return super().get_queryset().filter(recipient=self.request.user)


class NotificationListView(_Own, TenantScopedMixin, ListAPIView):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    required_roles = {"GET": ALL_ROLES}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(read_at__isnull=True)
        return qs.order_by("-created_at", "pk")


class NotificationReadView(_Own, TenantScopedMixin, GenericAPIView):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    required_roles = {"POST": ALL_ROLES}

    def post(self, request, **kwargs):
        n = self.get_object()
        if n.read_at is None:
            n.read_at = timezone.now()
            n.save(update_fields=["read_at"])
        return Response(NotificationSerializer(n).data)


class NotificationReadAllView(TenantScopedMixin, APIView):
    required_roles = {"POST": ALL_ROLES}

    def post(self, request, **kwargs):
        n = Notification.objects.filter(workspace_id=request.membership.workspace_id,
                                        recipient=request.user, read_at__isnull=True
                                        ).update(read_at=timezone.now())
        return Response({"marked_read": n})

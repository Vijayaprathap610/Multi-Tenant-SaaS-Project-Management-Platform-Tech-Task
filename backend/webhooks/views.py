import secrets
import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from audit.services import record
from billing.services import enforce_limit
from tenancy.mixins import TenantScopedMixin
from workspaces.models import MANAGE_ROLES

from .models import WebhookDelivery, WebhookEndpoint
from .serializers import DeliverySerializer, EndpointSerializer
from .tasks import deliver_webhook


def new_secret():
    return "whsec_" + secrets.token_urlsafe(32)[:40]


class EndpointListCreateView(TenantScopedMixin, ListCreateAPIView):
    serializer_class = EndpointSerializer
    queryset = WebhookEndpoint.objects.order_by("-created_at", "pk")
    required_roles = {"GET": MANAGE_ROLES, "POST": MANAGE_ROLES}

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        enforce_limit(request.membership.workspace, "webhooks")
        secret = new_secret()
        ep = s.save(workspace=request.membership.workspace, created_by=request.user, secret=secret)
        record("webhook.created", actor=request.user, workspace=ep.workspace, resource=ep,
               metadata={"events": ep.events})
        return Response({**EndpointSerializer(ep).data, "secret": secret}, status=201)  # shown once


class EndpointDetailView(TenantScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = EndpointSerializer
    queryset = WebhookEndpoint.objects.all()
    required_roles = {"GET": MANAGE_ROLES, "PATCH": MANAGE_ROLES, "DELETE": MANAGE_ROLES}

    def perform_update(self, serializer):
        ep = serializer.save()
        record("webhook.updated", actor=self.request.user, workspace=ep.workspace, resource=ep)

    def perform_destroy(self, instance):
        record("webhook.deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"id": str(instance.pk)})
        instance.delete()


class RotateSecretView(TenantScopedMixin, GenericAPIView):
    queryset = WebhookEndpoint.objects.all()
    required_roles = {"POST": MANAGE_ROLES}

    def post(self, request, **kwargs):
        ep = self.get_object()
        secret = new_secret()
        ep.secret = secret
        ep.save(update_fields=["secret"])
        record("webhook.secret_rotated", actor=request.user, workspace=ep.workspace, resource=ep)
        return Response({"secret": secret})


class DeliveryListView(TenantScopedMixin, ListAPIView):
    serializer_class = DeliverySerializer
    queryset = WebhookDelivery.objects.order_by("-created_at", "pk")
    required_roles = {"GET": MANAGE_ROLES}

    def get_queryset(self):
        # 404 (not an empty list) when the endpoint is not in the caller's workspace
        get_object_or_404(WebhookEndpoint.objects.filter(workspace_id=self.request.membership.workspace_id),
                          pk=self.kwargs["pk"])
        return super().get_queryset().filter(endpoint_id=self.kwargs["pk"])


class SendTestEventView(TenantScopedMixin, GenericAPIView):
    queryset = WebhookEndpoint.objects.all()
    required_roles = {"POST": MANAGE_ROLES}

    def post(self, request, **kwargs):
        ep = self.get_object()
        d = WebhookDelivery.objects.create(
            workspace_id=ep.workspace_id, endpoint=ep, event_id=uuid.uuid4(), event_type="ping",
            payload={"workspace_id": str(ep.workspace_id), "message": "Test event from Tech Task"})
        transaction.on_commit(lambda: deliver_webhook.delay(str(d.pk)))
        return Response({"delivery_id": str(d.pk)}, status=202)

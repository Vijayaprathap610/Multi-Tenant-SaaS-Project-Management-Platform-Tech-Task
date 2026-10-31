from rest_framework.generics import ListAPIView

from tenancy.mixins import TenantScopedMixin
from workspaces.models import MANAGE_ROLES

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditListView(TenantScopedMixin, ListAPIView):
    """Read-only; Owner/Admin only; always limited to the verified workspace."""
    serializer_class = AuditEventSerializer
    queryset = AuditEvent.objects.select_related("actor").order_by("-created_at")
    required_roles = {"GET": MANAGE_ROLES}

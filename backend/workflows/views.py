from rest_framework.exceptions import ValidationError
from rest_framework.generics import (DestroyAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)

from audit.services import record
from projects.mixins import ProjectScopedMixin
from projects.views import PM_UP
from workspaces.models import ALL_ROLES

from .models import WorkflowStatus, WorkflowTransition
from .serializers import StatusSerializer, TransitionSerializer


class StatusListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = StatusSerializer
    queryset = WorkflowStatus.objects.all()
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def perform_create(self, serializer):
        super().perform_create(serializer)
        s = serializer.instance
        record("workflow.status_created", actor=self.request.user, workspace=s.workspace, resource=s,
               metadata={"name": s.name})


class StatusDetailView(ProjectScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = StatusSerializer
    queryset = WorkflowStatus.objects.all()
    required_roles = {"GET": ALL_ROLES, "PATCH": PM_UP, "DELETE": PM_UP}

    def perform_update(self, serializer):
        s = serializer.save()
        record("workflow.status_updated", actor=self.request.user, workspace=s.workspace, resource=s)

    def perform_destroy(self, instance):
        if instance.issues.exists():
            raise ValidationError({"detail": "Move or delete the issues in this status first."})
        record("workflow.status_deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"name": instance.name})
        instance.delete()


class TransitionListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = TransitionSerializer
    queryset = WorkflowTransition.objects.all()
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def perform_create(self, serializer):
        super().perform_create(serializer)
        t = serializer.instance
        record("workflow.transition_created", actor=self.request.user, workspace=t.workspace, resource=t)


class TransitionDetailView(ProjectScopedMixin, DestroyAPIView):
    queryset = WorkflowTransition.objects.all()
    required_roles = {"DELETE": PM_UP}

    def perform_destroy(self, instance):
        record("workflow.transition_deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"id": str(instance.pk)})
        instance.delete()

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.response import Response

from audit.services import record
from issues.models import Issue
from projects.mixins import ProjectScopedMixin
from projects.views import PM_UP
from webhooks.emit import emit
from workflows.models import StatusCategory
from workspaces.models import ALL_ROLES

from .models import Sprint, SprintStatus
from .serializers import AssignIssuesSerializer, CompleteSprintSerializer, SprintSerializer


class SprintListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = SprintSerializer
    queryset = Sprint.objects.order_by("-start_date", "pk")
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get("status")
        return qs.filter(status=status) if status else qs

    def perform_create(self, serializer):
        super().perform_create(serializer)
        s = serializer.instance
        record("sprint.created", actor=self.request.user, workspace=s.workspace, resource=s)


class SprintDetailView(ProjectScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = SprintSerializer
    queryset = Sprint.objects.all()
    required_roles = {"GET": ALL_ROLES, "PATCH": PM_UP, "DELETE": PM_UP}

    def perform_update(self, serializer):
        s = serializer.save()
        record("sprint.updated", actor=self.request.user, workspace=s.workspace, resource=s)

    def perform_destroy(self, instance):
        if instance.status != SprintStatus.PLANNED:
            raise ValidationError({"detail": "Only planned sprints can be deleted."})
        record("sprint.deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"name": instance.name})
        instance.delete()


class SprintStartView(ProjectScopedMixin, GenericAPIView):
    queryset = Sprint.objects.all()
    required_roles = {"POST": PM_UP}

    def post(self, request, **kwargs):
        sprint = self.get_object()
        if sprint.status != SprintStatus.PLANNED:
            raise ValidationError({"detail": "Only a planned sprint can be started."})
        try:
            with transaction.atomic():
                sprint.status = SprintStatus.ACTIVE
                sprint.save(update_fields=["status"])
        except IntegrityError:  # partial unique index: one active sprint per project
            raise ValidationError({"detail": "This project already has an active sprint."})
        record("sprint.started", actor=request.user, workspace=sprint.workspace, resource=sprint)
        emit("sprint.started", workspace_id=sprint.workspace_id, actor=request.user,
             data={"sprint_id": str(sprint.pk), "name": sprint.name, "project_id": str(sprint.project_id)})
        return Response(SprintSerializer(sprint).data)


class SprintCompleteView(ProjectScopedMixin, GenericAPIView):
    queryset = Sprint.objects.all()
    serializer_class = CompleteSprintSerializer
    required_roles = {"POST": PM_UP}

    @transaction.atomic
    def post(self, request, **kwargs):
        sprint = self.get_object()
        if sprint.status != SprintStatus.ACTIVE:
            raise ValidationError({"detail": "Only an active sprint can be completed."})
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        target = s.validated_data["move_incomplete_to"]  # a planned sprint of this project, or None
        unfinished = Issue.objects.filter(sprint=sprint).exclude(status__category=StatusCategory.DONE)
        moved = unfinished.update(sprint=target)  # None = back to the backlog
        sprint.status = SprintStatus.COMPLETED
        sprint.completed_at = timezone.now()
        sprint.save(update_fields=["status", "completed_at"])
        record("sprint.completed", actor=request.user, workspace=sprint.workspace, resource=sprint,
               metadata={"incomplete_moved": moved, "to": str(target.pk) if target else "backlog"})
        emit("sprint.completed", workspace_id=sprint.workspace_id, actor=request.user,
             data={"sprint_id": str(sprint.pk), "name": sprint.name, "project_id": str(sprint.project_id),
                   "incomplete_moved": moved})
        return Response({**SprintSerializer(sprint).data, "incomplete_moved": moved})


class SprintIssuesView(ProjectScopedMixin, GenericAPIView):
    """Bulk-assign issues. Every id must belong to this project, otherwise nothing changes."""
    queryset = Sprint.objects.all()
    serializer_class = AssignIssuesSerializer
    required_roles = {"POST": PM_UP}

    @transaction.atomic
    def post(self, request, **kwargs):
        sprint = self.get_object()
        if sprint.status == SprintStatus.COMPLETED:
            raise ValidationError({"detail": "Cannot assign issues to a completed sprint."})
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        ids = set(s.validated_data["issue_ids"])
        issues = Issue.objects.filter(project=request.project, pk__in=ids)
        if issues.count() != len(ids):
            raise ValidationError({"issue_ids": "One or more issues were not found in this project."})
        issues.update(sprint=sprint)
        record("sprint.issues_assigned", actor=request.user, workspace=sprint.workspace,
               resource=sprint, metadata={"count": len(ids)})
        return Response({"assigned": len(ids)})


class SprintReportView(ProjectScopedMixin, GenericAPIView):
    queryset = Sprint.objects.all()
    required_roles = {"GET": ALL_ROLES}

    def get(self, request, **kwargs):
        sprint = self.get_object()
        counts = {c: 0 for c in StatusCategory.values}
        for row in Issue.objects.filter(sprint=sprint).values_list("status__category", flat=True):
            counts[row] += 1
        total = sum(counts.values())
        return Response({"sprint": SprintSerializer(sprint).data, "total_issues": total,
                         "by_category": counts,
                         "completion_rate": round(counts["done"] / total, 3) if total else 0.0})

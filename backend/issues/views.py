from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from audit.services import record
from projects.mixins import ProjectScopedMixin
from projects.models import Project
from webhooks.emit import emit
from workflows.models import WorkflowStatus
from workspaces.models import ALL_ROLES, Role

from .filters import filter_issues, order_issues
from .models import Issue
from .serializers import IssueSerializer, MoveSerializer
from .services import audit_status_change, check_transition, position_for

BASE_QS = Issue.objects.select_related("status", "assignee", "reporter", "project")


class IssueListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = IssueSerializer
    queryset = BASE_QS
    required_roles = {"GET": ALL_ROLES, "POST": ALL_ROLES}

    def get_queryset(self):
        return order_issues(filter_issues(super().get_queryset(), self.request), self.request)

    @transaction.atomic
    def perform_create(self, serializer):
        project = Project.objects.select_for_update().get(pk=self.request.project.pk)
        status = serializer.validated_data.get("status") or WorkflowStatus.objects.filter(
            project=project).order_by("position", "created_at").first()
        project.issue_counter += 1
        project.save(update_fields=["issue_counter"])
        issue = serializer.save(
            workspace=self.request.membership.workspace, project=project, status=status,
            number=project.issue_counter, reporter=self.request.user,
            position=position_for(project, status, None))
        record("issue.created", actor=self.request.user, workspace=issue.workspace, resource=issue,
               metadata={"key": issue.key})
        base = {"issue_id": str(issue.pk), "key": issue.key, "project_id": str(project.pk)}
        emit("issue.created", workspace_id=issue.workspace_id, actor=self.request.user, issue=issue,
             data={**base, "title": issue.title})
        if issue.assignee_id:
            emit("issue.assigned", workspace_id=issue.workspace_id, actor=self.request.user, issue=issue,
                 data={**base, "assignee_id": issue.assignee_id})


class IssueDetailView(ProjectScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer
    queryset = BASE_QS
    required_roles = {"GET": ALL_ROLES, "PATCH": ALL_ROLES, "DELETE": ALL_ROLES}

    @transaction.atomic
    def perform_update(self, serializer):
        old_status = serializer.instance.status
        old_assignee = serializer.instance.assignee_id
        changed = sorted(k for k in serializer.validated_data if k != "status")
        issue = serializer.save()
        base = {"issue_id": str(issue.pk), "key": issue.key, "project_id": str(issue.project_id)}
        if issue.status_id != old_status.pk:
            audit_status_change(self.request.user, issue, old_status, issue.status)
            emit("issue.status_changed", workspace_id=issue.workspace_id, actor=self.request.user,
                 issue=issue, data={**base, "from": old_status.name, "to": issue.status.name})
        if issue.assignee_id and issue.assignee_id != old_assignee:
            emit("issue.assigned", workspace_id=issue.workspace_id, actor=self.request.user, issue=issue,
                 data={**base, "assignee_id": issue.assignee_id})
        if changed:
            record("issue.updated", actor=self.request.user, workspace=issue.workspace,
                   resource=issue, metadata={"fields": changed, "key": issue.key})

    def perform_destroy(self, instance):
        m = self.request.membership
        # Plain Members may delete only issues they reported.
        if m.role == Role.MEMBER and instance.reporter_id != self.request.user.id:
            raise PermissionDenied("Members can delete only their own issues.")
        record("issue.deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"key": instance.key, "issue_id": str(instance.pk)})
        emit("issue.deleted", workspace_id=instance.workspace_id, actor=self.request.user,
             data={"issue_id": str(instance.pk), "key": instance.key, "project_id": str(instance.project_id)})
        instance.delete()


class IssueMoveView(ProjectScopedMixin, GenericAPIView):
    """Kanban drop target: validates the workflow transition on the server and persists
    the new column and position atomically."""
    serializer_class = MoveSerializer
    queryset = BASE_QS
    required_roles = {"POST": ALL_ROLES}

    @transaction.atomic
    def post(self, request, **kwargs):
        issue = self.get_object()
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        new_status = s.validated_data["status"]
        old_status = issue.status
        check_transition(request.project, old_status, new_status)
        issue.position = position_for(request.project, new_status,
                                      s.validated_data["before_issue_id"], exclude_pk=issue.pk)
        issue.status = new_status
        issue.save(update_fields=["status", "position", "updated_at"])
        if old_status.pk != new_status.pk:
            audit_status_change(request.user, issue, old_status, new_status)
            emit("issue.status_changed", workspace_id=issue.workspace_id, actor=request.user, issue=issue,
                 data={"issue_id": str(issue.pk), "key": issue.key, "project_id": str(issue.project_id),
                       "from": old_status.name, "to": new_status.name})
        return Response(IssueSerializer(issue, context=self.get_serializer_context()).data)

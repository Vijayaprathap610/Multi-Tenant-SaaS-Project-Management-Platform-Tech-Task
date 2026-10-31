from django.shortcuts import get_object_or_404
from rest_framework.generics import (GenericAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.response import Response

from audit.services import record
from issues.filters import filter_issues
from issues.models import Issue
from issues.serializers import IssueBriefSerializer
from projects.mixins import ProjectScopedMixin
from projects.views import PM_UP
from workspaces.models import ALL_ROLES

from .models import Board, BoardColumn
from .serializers import BoardSerializer, ColumnSerializer

KANBAN_ISSUE_LIMIT = 500


class BoardListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = BoardSerializer
    queryset = Board.objects.prefetch_related("columns").order_by("created_at")
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def perform_create(self, serializer):
        super().perform_create(serializer)
        b = serializer.instance
        record("board.created", actor=self.request.user, workspace=b.workspace, resource=b)


class BoardDetailView(ProjectScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = BoardSerializer
    queryset = Board.objects.prefetch_related("columns")
    required_roles = {"GET": ALL_ROLES, "PATCH": PM_UP, "DELETE": PM_UP}

    def perform_update(self, serializer):
        b = serializer.save()
        record("board.updated", actor=self.request.user, workspace=b.workspace, resource=b)

    def perform_destroy(self, instance):
        record("board.deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"name": instance.name})
        instance.delete()


class _BoardChildMixin(ProjectScopedMixin):
    project_filter_field = "board__project_id"

    def get_board(self):
        return get_object_or_404(Board.objects.filter(project=self.request.project),
                                 pk=self.kwargs["board_id"])

    def get_queryset(self):
        return super().get_queryset().filter(board_id=self.kwargs["board_id"]).select_related("board")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["board"] = self.get_board()
        return ctx


class ColumnListCreateView(_BoardChildMixin, ListCreateAPIView):
    serializer_class = ColumnSerializer
    queryset = BoardColumn.objects.all()
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def perform_create(self, serializer):
        col = serializer.save(workspace=self.request.membership.workspace, board=self.get_board())
        record("board.column_created", actor=self.request.user, workspace=col.workspace, resource=col)


class ColumnDetailView(_BoardChildMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ColumnSerializer
    queryset = BoardColumn.objects.all()
    required_roles = {"GET": ALL_ROLES, "PATCH": PM_UP, "DELETE": PM_UP}

    def perform_update(self, serializer):
        col = serializer.save()
        record("board.column_updated", actor=self.request.user, workspace=col.workspace, resource=col)

    def perform_destroy(self, instance):
        record("board.column_deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"name": instance.name})
        instance.delete()


class KanbanView(ProjectScopedMixin, GenericAPIView):
    """One board with its columns and issues in a constant number of queries
    (board, columns+status, issues+assignee) regardless of how many issues exist."""
    queryset = Board.objects.all()
    required_roles = {"GET": ALL_ROLES}

    def get(self, request, **kwargs):
        board = get_object_or_404(self.get_queryset(), pk=kwargs["board_id"])
        columns = list(board.columns.select_related("status").order_by("position"))
        issues = filter_issues(
            Issue.objects.filter(project=request.project, status_id__in=[c.status_id for c in columns])
            .select_related("assignee", "status", "project"), request).order_by("position", "pk")[:KANBAN_ISSUE_LIMIT]
        by_status = {c.status_id: [] for c in columns}
        for issue in issues:
            by_status[issue.status_id].append(IssueBriefSerializer(issue).data)
        return Response({
            "id": str(board.pk), "name": board.name,
            "columns": [{"id": str(c.pk), "name": c.name, "status_id": str(c.status_id),
                         "category": c.status.category, "position": c.position,
                         "issues": by_status[c.status_id]} for c in columns],
            "truncated": len(issues) == KANBAN_ISSUE_LIMIT,
        })

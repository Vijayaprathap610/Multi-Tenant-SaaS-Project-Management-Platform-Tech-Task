import csv

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response

from audit.services import record
from issues.models import Issue
from projects.mixins import ProjectScopedMixin
from projects.views import PM_UP

from .models import Report
from .serializers import ReportSerializer
from .tasks import generate_project_report


class ReportListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = ReportSerializer
    queryset = Report.objects.order_by("-created_at", "pk")
    required_roles = {"GET": PM_UP, "POST": PM_UP}

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            report = Report.objects.create(workspace=request.membership.workspace, project=request.project,
                                           requested_by=request.user)
            record("report.requested", actor=request.user, workspace=report.workspace, resource=report)
            transaction.on_commit(lambda: generate_project_report.delay(str(report.pk)))
        return Response(ReportSerializer(report).data, status=202)


class ReportDetailView(ProjectScopedMixin, RetrieveAPIView):
    serializer_class = ReportSerializer
    queryset = Report.objects.all()
    required_roles = {"GET": PM_UP}


class _Echo:
    def write(self, value):
        return value


def _safe(cell):
    """Neutralise spreadsheet formula injection."""
    s = "" if cell is None else str(cell)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


class IssueExportView(ProjectScopedMixin, GenericAPIView):
    """CSV export of this project's issues only (Owner/Admin/PM)."""
    queryset = Issue.objects.all()
    required_roles = {"GET": PM_UP}

    def get(self, request, **kwargs):
        qs = (Issue.objects.filter(project=request.project, workspace_id=request.membership.workspace_id)
              .select_related("status", "assignee", "reporter", "project").order_by("number"))
        writer = csv.writer(_Echo())

        def rows():
            yield writer.writerow(["key", "title", "status", "priority", "assignee", "reporter", "due_date"])
            for i in qs.iterator(chunk_size=500):
                yield writer.writerow([_safe(x) for x in (
                    i.key, i.title, i.status.name, i.priority, i.assignee.email if i.assignee else "",
                    i.reporter.email if i.reporter else "", i.due_date)])

        record("report.issues_exported", actor=request.user, workspace=request.membership.workspace,
               metadata={"project_id": str(request.project.pk)})
        resp = StreamingHttpResponse(rows(), content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{request.project.key}-issues.csv"'
        resp["X-Content-Type-Options"] = "nosniff"
        return resp

from celery import shared_task
from django.db import OperationalError
from django.utils import timezone

from projects.access import user_has_project_access

from .builder import build_report
from .models import Report, ReportStatus


def _fail(report, reason):
    report.status = ReportStatus.FAILED
    report.error = reason
    report.completed_at = timezone.now()
    report.save(update_fields=["status", "error", "completed_at"])


@shared_task(autoretry_for=(OperationalError,), retry_backoff=True, max_retries=3, time_limit=120)
def generate_project_report(report_id):
    """Idempotent (only runs for pending reports) and authorization-aware: the project must be in the
    report's workspace and the requester must still have access to it when the job runs."""
    report = Report.objects.select_related("project").filter(pk=report_id).first()
    if report is None or report.status != ReportStatus.PENDING:
        return
    project = report.project
    if project.workspace_id != report.workspace_id:
        return _fail(report, "Invalid project.")
    if report.requested_by_id is None or not user_has_project_access(report.requested_by_id, project):
        return _fail(report, "Requester no longer has access.")
    report.data = build_report(project)
    report.status = ReportStatus.READY
    report.completed_at = timezone.now()
    report.save(update_fields=["data", "status", "completed_at"])

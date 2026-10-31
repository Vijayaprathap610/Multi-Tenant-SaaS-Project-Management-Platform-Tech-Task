from django.db.models import Count
from django.utils import timezone

from issues.models import Issue
from sprints.models import Sprint, SprintStatus
from workflows.models import StatusCategory


def build_report(project):
    """Aggregates in a handful of queries (no per-row access), always filtered by project."""
    issues = Issue.objects.filter(project=project)
    by_status = list(issues.values("status__name", "status__category").annotate(n=Count("id"))
                     .order_by("status__position"))
    by_priority = {r["priority"]: r["n"] for r in issues.values("priority").annotate(n=Count("id"))}
    by_assignee = {(r["assignee__email"] or "Unassigned"): r["n"]
                   for r in issues.values("assignee__email").annotate(n=Count("id"))}
    total = sum(r["n"] for r in by_status)
    done = sum(r["n"] for r in by_status if r["status__category"] == StatusCategory.DONE)
    overdue = issues.filter(due_date__lt=timezone.localdate()).exclude(
        status__category=StatusCategory.DONE).count()
    sprints = []
    for sp in Sprint.objects.filter(project=project).exclude(status=SprintStatus.PLANNED).order_by("-start_date")[:10]:
        counts = dict(Issue.objects.filter(sprint=sp).values_list("status__category").annotate(n=Count("id")))
        s_total = sum(counts.values())
        sprints.append({"name": sp.name, "status": sp.status, "total": s_total,
                        "done": counts.get(StatusCategory.DONE, 0)})
    return {"total_issues": total, "done_issues": done,
            "completion_rate": round(done / total, 3) if total else 0.0, "overdue_issues": overdue,
            "by_status": [{"status": r["status__name"], "count": r["n"]} for r in by_status],
            "by_priority": by_priority, "by_assignee": by_assignee, "sprints": sprints}

from tenancy.query import apply_ordering, uuid_param

ORDERING = {"created_at", "updated_at", "priority", "due_date", "number", "title"}


def filter_issues(qs, request):
    p = request.query_params
    for param, field in (("status", "status_id"), ("sprint", "sprint_id")):
        value = uuid_param(request, param)
        if value is not None:
            qs = qs.filter(**{field: value})
    if p.get("assignee"):
        qs = qs.filter(assignee_id=p["assignee"]) if p["assignee"].isdigit() else qs.none()
    if p.get("priority"):
        qs = qs.filter(priority=p["priority"])
    if p.get("label"):
        qs = qs.filter(labels__contains=[p["label"]])
    if p.get("q"):
        qs = qs.filter(title__icontains=p["q"])
    if p.get("backlog") == "true":
        qs = qs.filter(sprint__isnull=True)
    return qs


def order_issues(qs, request):
    return apply_ordering(qs, request, ORDERING, "-created_at")

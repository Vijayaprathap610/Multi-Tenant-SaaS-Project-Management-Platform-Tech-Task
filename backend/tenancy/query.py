import uuid

from rest_framework.exceptions import ValidationError


def uuid_param(request, name):
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise ValidationError({name: "Must be a valid UUID."})


def apply_ordering(qs, request, allowed, default):
    ordering = request.query_params.get("ordering", default)
    if ordering.lstrip("-") not in allowed:
        ordering = default
    return qs.order_by(ordering, "pk")  # pk tiebreak keeps pagination stable

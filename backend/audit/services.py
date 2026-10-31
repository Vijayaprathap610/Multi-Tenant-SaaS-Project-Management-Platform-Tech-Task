from .models import AuditEvent


def record(event_type, *, actor=None, workspace=None, resource=None, metadata=None):
    """resource: any model instance (stored as type name + pk string)."""
    return AuditEvent.objects.create(
        event_type=event_type,
        actor=actor if getattr(actor, "is_authenticated", True) else None,
        workspace=workspace,
        resource_type=type(resource).__name__ if resource is not None else "",
        resource_id=str(resource.pk) if resource is not None else "",
        metadata=metadata or {},
    )

from .models import StatusCategory, WorkflowStatus, WorkflowTransition

DEFAULTS = [("To Do", StatusCategory.TODO), ("In Progress", StatusCategory.IN_PROGRESS),
            ("Done", StatusCategory.DONE)]
# Deliberately not fully connected: To Do -> Done is not allowed out of the box.
DEFAULT_TRANSITIONS = [(0, 1), (1, 0), (1, 2), (2, 1)]


def seed_default_workflow(project):
    statuses = [WorkflowStatus.objects.create(workspace_id=project.workspace_id, project=project,
                                              name=n, category=c, position=i)
                for i, (n, c) in enumerate(DEFAULTS)]
    for a, b in DEFAULT_TRANSITIONS:
        WorkflowTransition.objects.create(workspace_id=project.workspace_id, project=project,
                                          from_status=statuses[a], to_status=statuses[b])
    return statuses

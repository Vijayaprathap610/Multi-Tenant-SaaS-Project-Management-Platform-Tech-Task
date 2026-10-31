def create_project_defaults(project):
    """Every project starts with a workflow and a Kanban board so it is usable immediately."""
    from boards.services import create_default_board
    from workflows.services import seed_default_workflow

    statuses = seed_default_workflow(project)
    create_default_board(project, statuses)

from .models import Board, BoardColumn


def create_default_board(project, statuses):
    board = Board.objects.create(workspace_id=project.workspace_id, project=project, name="Main board")
    for i, s in enumerate(statuses):
        BoardColumn.objects.create(workspace_id=project.workspace_id, board=board, name=s.name,
                                   status=s, position=i)
    return board

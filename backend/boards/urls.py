from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/boards/"
urlpatterns = [
    path(P, views.BoardListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.BoardDetailView.as_view()),
    path(P + "<uuid:board_id>/kanban/", views.KanbanView.as_view()),
    path(P + "<uuid:board_id>/columns/", views.ColumnListCreateView.as_view()),
    path(P + "<uuid:board_id>/columns/<uuid:pk>/", views.ColumnDetailView.as_view()),
]

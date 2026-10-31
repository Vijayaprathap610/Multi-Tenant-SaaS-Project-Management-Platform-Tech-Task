from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/issues/<uuid:issue_id>/comments/"
urlpatterns = [
    path(P, views.CommentListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.CommentDetailView.as_view()),
]

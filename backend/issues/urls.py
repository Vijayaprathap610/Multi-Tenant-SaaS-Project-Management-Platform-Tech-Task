from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/issues/"
urlpatterns = [
    path(P, views.IssueListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.IssueDetailView.as_view()),
    path(P + "<uuid:pk>/move/", views.IssueMoveView.as_view()),
]

from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/sprints/"
urlpatterns = [
    path(P, views.SprintListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.SprintDetailView.as_view()),
    path(P + "<uuid:pk>/start/", views.SprintStartView.as_view()),
    path(P + "<uuid:pk>/complete/", views.SprintCompleteView.as_view()),
    path(P + "<uuid:pk>/issues/", views.SprintIssuesView.as_view()),
    path(P + "<uuid:pk>/report/", views.SprintReportView.as_view()),
]

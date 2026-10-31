from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/reports/"
urlpatterns = [
    path(P, views.ReportListCreateView.as_view()),
    path(P + "export/issues/", views.IssueExportView.as_view()),
    path(P + "<uuid:pk>/", views.ReportDetailView.as_view()),
]

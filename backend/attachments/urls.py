from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/issues/<uuid:issue_id>/attachments/"
urlpatterns = [
    path(P, views.AttachmentListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.AttachmentDetailView.as_view()),
    path(P + "<uuid:pk>/download/", views.AttachmentDownloadView.as_view()),
]

from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/"
urlpatterns = [
    path(P, views.ProjectListCreateView.as_view(), name="project-list"),
    path(P + "<uuid:project_id>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path(P + "<uuid:project_id>/members/", views.ProjectMemberListCreateView.as_view()),
    path(P + "<uuid:project_id>/members/<uuid:pk>/", views.ProjectMemberDetailView.as_view()),
]

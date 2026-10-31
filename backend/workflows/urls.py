from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/projects/<uuid:project_id>/"
urlpatterns = [
    path(P + "statuses/", views.StatusListCreateView.as_view()),
    path(P + "statuses/<uuid:pk>/", views.StatusDetailView.as_view()),
    path(P + "transitions/", views.TransitionListCreateView.as_view()),
    path(P + "transitions/<uuid:pk>/", views.TransitionDetailView.as_view()),
]

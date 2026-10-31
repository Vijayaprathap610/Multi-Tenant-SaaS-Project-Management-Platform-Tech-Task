from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/notifications/"
urlpatterns = [
    path(P, views.NotificationListView.as_view()),
    path(P + "read-all/", views.NotificationReadAllView.as_view()),
    path(P + "<uuid:pk>/read/", views.NotificationReadView.as_view()),
]

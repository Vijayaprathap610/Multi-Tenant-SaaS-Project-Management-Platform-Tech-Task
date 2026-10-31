from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/webhooks/"
urlpatterns = [
    path(P, views.EndpointListCreateView.as_view()),
    path(P + "<uuid:pk>/", views.EndpointDetailView.as_view()),
    path(P + "<uuid:pk>/rotate-secret/", views.RotateSecretView.as_view()),
    path(P + "<uuid:pk>/deliveries/", views.DeliveryListView.as_view()),
    path(P + "<uuid:pk>/test/", views.SendTestEventView.as_view()),
]

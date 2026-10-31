from django.urls import path

from . import views

P = "workspaces/<uuid:workspace_id>/billing/"
urlpatterns = [
    path(P, views.BillingStatusView.as_view()),
    path(P + "checkout/", views.CheckoutView.as_view()),
    path(P + "portal/", views.PortalView.as_view()),
    path(P + "cancel/", views.CancelView.as_view()),
    path("billing/webhook/", views.StripeWebhookView.as_view()),
]

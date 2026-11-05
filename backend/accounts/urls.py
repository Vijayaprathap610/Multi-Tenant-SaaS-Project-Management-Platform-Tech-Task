from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view()),
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("auth/change-password/", views.ChangePasswordView.as_view()),
    path("auth/password-reset/", views.PasswordResetRequestView.as_view()),
    path("auth/password-reset/confirm/", views.PasswordResetConfirmView.as_view()),
    path("platform-admin/login/", views.PlatformAdminLoginView.as_view()),
    path("platform-admin/stats/", views.PlatformAdminStatsView.as_view()),
    path("platform-admin/analytics/", views.PlatformAdminAnalyticsView.as_view()),
    path("platform-admin/companies/", views.PlatformAdminCompaniesView.as_view()),
    path("platform-admin/companies/<uuid:workspace_id>/", views.PlatformAdminCompanyDetailView.as_view()),
    path("platform-admin/subscriptions/", views.PlatformAdminSubscriptionsView.as_view()),
    path("platform-admin/subscriptions/<uuid:workspace_id>/", views.PlatformAdminSubscriptionDetailView.as_view()),
    path("platform-admin/users/", views.PlatformAdminUsersView.as_view()),
    path("platform-admin/users/<int:user_id>/", views.PlatformAdminUserDetailView.as_view()),
    path("platform-admin/activity/", views.PlatformAdminActivityView.as_view()),
    path("platform-admin/settings/", views.PlatformAdminSettingsView.as_view()),
]

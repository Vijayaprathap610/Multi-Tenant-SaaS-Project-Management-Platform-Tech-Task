from django.urls import include, path

urlpatterns = [
    path("api/", include("accounts.urls")),
    path("api/", include("workspaces.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("projects.urls")),
    path("api/", include("workflows.urls")),
    path("api/", include("boards.urls")),
    path("api/", include("sprints.urls")),
    path("api/", include("issues.urls")),
    path("api/", include("comments.urls")),
    path("api/", include("attachments.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("webhooks.urls")),
    path("api/", include("reports.urls")),
    path("api/", include("billing.urls")),
]

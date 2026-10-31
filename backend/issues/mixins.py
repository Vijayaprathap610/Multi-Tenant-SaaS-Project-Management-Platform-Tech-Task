from django.shortcuts import get_object_or_404

from projects.mixins import ProjectScopedMixin

from .models import Issue


class IssueChildMixin(ProjectScopedMixin):
    """For resources nested under /issues/<issue_id>/ (comments, attachments).
    The issue is looked up inside the verified project, so a foreign issue id is a 404."""

    def get_issue(self):
        if not hasattr(self, "_issue"):
            self._issue = get_object_or_404(
                Issue.objects.select_related("project").filter(project=self.request.project),
                pk=self.kwargs["issue_id"])
        return self._issue

    def get_queryset(self):
        self.get_issue()
        return super().get_queryset().filter(issue_id=self.kwargs["issue_id"])

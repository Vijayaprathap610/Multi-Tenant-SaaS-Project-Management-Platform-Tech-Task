from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from audit.services import record
from issues.mixins import IssueChildMixin
from projects.views import PM_UP
from webhooks.emit import emit
from workspaces.models import ALL_ROLES

from .models import Comment
from .serializers import CommentSerializer


class CommentListCreateView(IssueChildMixin, ListCreateAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related("author").order_by("created_at", "pk")
    required_roles = {"GET": ALL_ROLES, "POST": ALL_ROLES}

    def perform_create(self, serializer):
        issue = self.get_issue()
        c = serializer.save(workspace=self.request.membership.workspace, project=self.request.project,
                            issue=issue, author=self.request.user)
        emit("comment.created", workspace_id=c.workspace_id, actor=self.request.user, issue=issue,
             data={"comment_id": str(c.pk), "issue_id": str(issue.pk), "key": issue.key,
                   "project_id": str(issue.project_id)})


class CommentDetailView(IssueChildMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related("author")
    required_roles = {"GET": ALL_ROLES, "PATCH": ALL_ROLES, "DELETE": ALL_ROLES}

    def perform_update(self, serializer):
        if serializer.instance.author_id != self.request.user.id:
            raise PermissionDenied("Only the author can edit a comment.")
        serializer.save(edited_at=timezone.now())

    def perform_destroy(self, instance):
        is_author = instance.author_id == self.request.user.id
        if not is_author and self.request.membership.role not in PM_UP:
            raise PermissionDenied("Only the author or a project manager can delete a comment.")
        if not is_author:
            record("comment.deleted_by_moderator", actor=self.request.user, workspace=instance.workspace,
                   resource=instance, metadata={"issue_id": str(instance.issue_id)})
        instance.delete()

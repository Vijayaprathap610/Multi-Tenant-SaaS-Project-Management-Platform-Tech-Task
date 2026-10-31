import hashlib

from django.db import transaction
from django.http import FileResponse
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from audit.services import record
from billing.services import enforce_limit
from issues.mixins import IssueChildMixin
from projects.views import PM_UP
from webhooks.emit import emit
from workspaces.models import ALL_ROLES

from .models import Attachment
from .scanning import scan_upload
from .serializers import AttachmentSerializer
from .validation import validate_upload


class AttachmentListCreateView(IssueChildMixin, ListCreateAPIView):
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.select_related("uploaded_by").order_by("-created_at", "pk")
    parser_classes = [MultiPartParser]
    required_roles = {"GET": ALL_ROLES, "POST": ALL_ROLES}

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        issue = self.get_issue()
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "No file was provided."})
        name, content_type = validate_upload(upload)
        enforce_limit(request.membership.workspace, "storage", add=upload.size)
        scan_upload(upload)
        digest = hashlib.sha256()
        for chunk in upload.chunks():
            digest.update(chunk)
        upload.seek(0)
        att = Attachment(workspace=request.membership.workspace, project=request.project, issue=issue,
                         uploaded_by=request.user, original_name=name, content_type=content_type,
                         size=upload.size, sha256=digest.hexdigest())
        att.file.save("ignored", upload, save=False)
        att.save()
        record("attachment.uploaded", actor=request.user, workspace=att.workspace, resource=att,
               metadata={"issue_id": str(issue.pk), "size": att.size})
        emit("attachment.uploaded", workspace_id=att.workspace_id, actor=request.user, issue=issue,
             data={"attachment_id": str(att.pk), "issue_id": str(issue.pk), "key": issue.key,
                   "project_id": str(issue.project_id), "name": att.original_name})
        return Response(AttachmentSerializer(att).data, status=201)


class AttachmentDownloadView(IssueChildMixin, GenericAPIView):
    """The only way to read a stored file: authenticated, tenant- and project-scoped.
    Always sent as a download with nosniff and a sandboxed CSP so uploads cannot execute in-browser."""
    queryset = Attachment.objects.all()
    required_roles = {"GET": ALL_ROLES}

    def get(self, request, **kwargs):
        att = self.get_object()
        record("attachment.downloaded", actor=request.user, workspace=att.workspace, resource=att)
        resp = FileResponse(att.file.open("rb"), as_attachment=True, filename=att.original_name,
                            content_type=att.content_type)
        resp["X-Content-Type-Options"] = "nosniff"
        resp["Content-Security-Policy"] = "sandbox; default-src 'none'"
        resp["Cache-Control"] = "private, no-store"
        return resp


class AttachmentDetailView(IssueChildMixin, GenericAPIView):
    queryset = Attachment.objects.all()
    required_roles = {"DELETE": ALL_ROLES}

    def delete(self, request, **kwargs):
        att = self.get_object()
        if att.uploaded_by_id != request.user.id and request.membership.role not in PM_UP:
            raise PermissionDenied("Only the uploader or a project manager can delete an attachment.")
        storage, name = att.file.storage, att.file.name
        record("attachment.deleted", actor=request.user, workspace=att.workspace,
               metadata={"issue_id": str(att.issue_id), "name": att.original_name})
        att.delete()
        transaction.on_commit(lambda: storage.delete(name))
        return Response(status=204)

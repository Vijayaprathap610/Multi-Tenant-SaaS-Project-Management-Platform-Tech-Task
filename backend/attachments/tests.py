import os
import tempfile

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from audit.models import AuditEvent
from issues.tests import IssueBase
from tenancy.testing import make_issue, make_project, make_tenant, purl

from .models import Attachment

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class AttachmentTests(IssueBase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._override = override_settings(MEDIA_ROOT=cls._tmp.name)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        cls._tmp.cleanup()

    def setUp(self):
        super().setUp()
        self.issue = make_issue(self.project, self.owner)
        self.aurl = purl(self.ws, self.project, f"issues/{self.issue.id}/attachments/")

    def _upload(self, name="shot.png", data=PNG, ctype="image/png"):
        return self.client.post(self.aurl, {"file": SimpleUploadedFile(name, data, content_type=ctype)},
                                format="multipart")

    def test_upload_download_roundtrip_with_safe_headers_and_no_path_leak(self):
        self.client.force_authenticate(self.member)
        r = self._upload()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(set(r.json()), {"id", "original_name", "content_type", "size", "uploaded_by_email", "created_at"})
        att = Attachment.objects.get()
        self.assertTrue(AuditEvent.objects.filter(event_type="attachment.uploaded", workspace=self.ws).exists())
        self.assertNotIn("shot", att.file.name)           # random storage name
        self.assertTrue(att.file.name.startswith(str(self.ws.id)))
        d = self.client.get(f"{self.aurl}{att.id}/download/")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(b"".join(d.streaming_content), PNG)
        self.assertIn("attachment", d["Content-Disposition"])
        self.assertEqual(d["X-Content-Type-Options"], "nosniff")
        self.assertIn("sandbox", d["Content-Security-Policy"])

    def test_dangerous_or_mismatched_files_rejected(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self._upload("run.exe", b"MZ\x90\x00").status_code, 400)
        self.assertEqual(self._upload("page.html", b"<script>alert(1)</script>", "text/html").status_code, 400)
        self.assertEqual(self._upload("fake.png", b"not a png at all").status_code, 400)  # content != extension
        self.assertEqual(self._upload("empty.txt", b"").status_code, 400)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_client_mime_type_is_ignored_and_filename_sanitised(self):
        self.client.force_authenticate(self.owner)
        r = self._upload("../../etc/pass wd.txt", b"hello", ctype="text/html")
        self.assertEqual(r.status_code, 201)
        att = Attachment.objects.get()
        self.assertEqual(att.content_type, "text/plain")
        self.assertEqual(att.original_name, "pass wd.txt")

    @override_settings(ATTACHMENT_MAX_BYTES=10)
    def test_size_limit(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self._upload("big.txt", b"x" * 11).status_code, 400)
        self.assertEqual(self._upload("ok.txt", b"x" * 10).status_code, 201)

    def test_malware_scan_hook_fails_closed(self):
        self.client.force_authenticate(self.owner)
        with override_settings(ATTACHMENT_SCAN_COMMAND="false"):
            self.assertEqual(self._upload("a.txt", b"hello").status_code, 400)
        with override_settings(ATTACHMENT_SCAN_COMMAND="definitely-not-a-real-scanner"):
            self.assertEqual(self._upload("a.txt", b"hello").status_code, 400)
        with override_settings(ATTACHMENT_SCAN_COMMAND="true"):
            self.assertEqual(self._upload("a.txt", b"hello").status_code, 201)

    def test_outsider_and_foreign_tenant_cannot_list_or_download(self):
        self.client.force_authenticate(self.owner)
        self._upload()
        att = Attachment.objects.get()
        self.client.force_authenticate(self.outsider)  # workspace member without project access
        self.assertEqual(self.client.get(self.aurl).status_code, 404)
        self.assertEqual(self.client.get(f"{self.aurl}{att.id}/download/").status_code, 404)
        ws_b, ub = make_tenant("B", "ob@b.test")
        self.client.force_authenticate(ub["owner"])
        self.assertEqual(self.client.get(f"/api/workspaces/{self.ws.id}/projects/{self.project.id}/"
                                         f"issues/{self.issue.id}/attachments/{att.id}/download/").status_code, 404)

    def test_delete_rules_and_file_removed(self):
        self.client.force_authenticate(self.owner)
        self._upload()
        att = Attachment.objects.get()
        path = att.file.path
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.delete(f"{self.aurl}{att.id}/").status_code, 403)
        self.client.force_authenticate(self.pm)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.delete(f"{self.aurl}{att.id}/").status_code, 204)
        self.assertFalse(os.path.exists(path))

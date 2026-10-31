import os
import re

from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
    ".webp": "image/webp", ".pdf": "application/pdf", ".txt": "text/plain", ".csv": "text/csv",
    ".md": "text/markdown", ".json": "application/json", ".zip": "application/zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
ZIP_LIKE = {".zip", ".docx", ".xlsx", ".pptx"}
MAGIC = {".png": [b"\x89PNG\r\n\x1a\n"], ".jpg": [b"\xff\xd8\xff"], ".jpeg": [b"\xff\xd8\xff"],
         ".gif": [b"GIF87a", b"GIF89a"], ".pdf": [b"%PDF-"]}
TEXT = {".txt", ".csv", ".md", ".json"}


def validate_upload(upload):
    """Returns (safe_display_name, server_decided_content_type) or raises ValidationError.
    The client's filename is used only for its extension and a sanitized display name; the
    client's MIME type is ignored."""
    name = os.path.basename((upload.name or "").replace("\\", "/"))
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED:
        raise ValidationError({"file": "This file type is not allowed."})
    if upload.size <= 0:
        raise ValidationError({"file": "The file is empty."})
    if upload.size > settings.ATTACHMENT_MAX_BYTES:
        raise ValidationError({"file": f"File exceeds the {settings.ATTACHMENT_MAX_BYTES // (1024 * 1024)} MB limit."})
    head = upload.read(8192)
    upload.seek(0)
    ok = True
    if ext in MAGIC:
        ok = any(head.startswith(m) for m in MAGIC[ext])
    elif ext == ".webp":
        ok = head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    elif ext in ZIP_LIKE:
        ok = head.startswith(b"PK\x03\x04")
    elif ext in TEXT:
        ok = b"\x00" not in head
    if not ok:
        raise ValidationError({"file": "File content does not match its extension."})
    safe = re.sub(r"[^\w.\- ]", "_", name)[:200] or f"file{ext}"
    return safe, ALLOWED[ext]

import shlex
import subprocess
import tempfile

from django.conf import settings
from rest_framework.exceptions import ValidationError


def scan_upload(upload):
    """Optional malware scan via an external command (ATTACHMENT_SCAN_COMMAND, e.g. clamdscan).
    Disabled when unset. When enabled it fails closed: any non-zero exit or error rejects the file."""
    cmd = settings.ATTACHMENT_SCAN_COMMAND
    if not cmd:
        return
    with tempfile.NamedTemporaryFile() as tmp:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp.flush()
        upload.seek(0)
        try:
            result = subprocess.run([*shlex.split(cmd), tmp.name], capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            raise ValidationError({"file": "Malware scan unavailable; upload rejected."})
    if result.returncode != 0:
        raise ValidationError({"file": "File failed the malware scan."})

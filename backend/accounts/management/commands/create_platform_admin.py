import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = ("Create the single Platform Administrator. Password comes from "
            "PLATFORM_ADMIN_PASSWORD or an interactive prompt; never from argv.")

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)

    def handle(self, *args, **opts):
        User = get_user_model()
        if User.objects.filter(is_platform_admin=True, is_active=True).exists():
            raise CommandError("An active Platform Administrator already exists. "
                               "Rotate credentials instead of creating another.")
        password = os.environ.get("PLATFORM_ADMIN_PASSWORD") or getpass.getpass("Password: ")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))
        User.objects.create_platform_admin(opts["email"], password)
        self.stdout.write(self.style.SUCCESS("Platform Administrator created."))

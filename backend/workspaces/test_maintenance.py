from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from comments.models import Comment
from issues.models import Issue
from notifications.models import Notification
from notifications.tasks import prune_notifications
from projects.models import Project
from tenancy.testing import BaseAPITest, make_issue, make_project, make_tenant

from .models import Invitation, Membership, Workspace
from .tasks import prune_invitations


class ScheduledMaintenanceTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.ws, u = make_tenant("A", "o@a.test", member="m@a.test")
        self.owner, self.member = u["owner"], u["member"]

    def test_prune_invitations_removes_only_old_finished_ones(self):
        now = timezone.now()
        old_expired = Invitation.objects.create(workspace=self.ws, email="a@x.test", role="member",
                                                expires_at=now - timedelta(days=45))
        fresh = Invitation.objects.create(workspace=self.ws, email="b@x.test", role="member",
                                          expires_at=now + timedelta(days=3))
        recently_expired = Invitation.objects.create(workspace=self.ws, email="c@x.test", role="member",
                                                     expires_at=now - timedelta(days=2))
        self.assertEqual(prune_invitations(), 1)
        self.assertFalse(Invitation.objects.filter(pk=old_expired.pk).exists())
        self.assertTrue(Invitation.objects.filter(pk__in=[fresh.pk, recently_expired.pk]).count() == 2)

    def test_prune_notifications_keeps_unread_and_recent(self):
        old = timezone.now() - timedelta(days=120)
        read_old = Notification.objects.create(workspace=self.ws, recipient=self.member, event_type="x",
                                               message="old read", dedupe_key="1", read_at=old)
        unread_old = Notification.objects.create(workspace=self.ws, recipient=self.member, event_type="x",
                                                 message="old unread", dedupe_key="2")
        recent_read = Notification.objects.create(workspace=self.ws, recipient=self.member, event_type="x",
                                                  message="recent read", dedupe_key="3", read_at=timezone.now())
        Notification.objects.filter(pk__in=[read_old.pk, unread_old.pk]).update(created_at=old)
        self.assertEqual(prune_notifications(), 1)
        self.assertEqual(set(Notification.objects.values_list("dedupe_key", flat=True)), {"2", "3"})


class SeedDemoCommandTests(BaseAPITest):
    def test_refuses_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Workspace.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_creates_two_isolated_demo_companies(self):
        out = StringIO()
        call_command("seed_demo", issues=6, stdout=out)
        self.assertEqual(Workspace.objects.count(), 2)
        self.assertEqual(Membership.objects.count(), 8)
        self.assertEqual(Issue.objects.count(), 12)
        for ws in Workspace.objects.all():
            self.assertEqual(Project.objects.filter(workspace=ws).count(), 1)
            self.assertFalse(Issue.objects.filter(workspace=ws).exclude(project__workspace=ws).exists())
        self.assertIn("Password for all demo users", out.getvalue())
        call_command("seed_demo", issues=6, stdout=StringIO())   # second run is a no-op
        self.assertEqual(Workspace.objects.count(), 2)

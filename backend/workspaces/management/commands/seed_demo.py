import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from billing.models import Subscription
from comments.models import Comment
from issues.models import Issue
from projects.models import Project, ProjectMember
from projects.services import create_project_defaults
from sprints.models import Sprint, SprintStatus
from workflows.models import WorkflowStatus
from workspaces.models import Membership, Role, Workspace

User = get_user_model()
TITLES = ["Set up CI pipeline", "Design login screen", "Fix password reset email", "Add CSV export",
          "Kanban card colours", "Write API docs", "Rate-limit login", "Improve board performance",
          "Upload validation", "Webhook retry logging", "Sprint report", "Onboarding copy"]


class Command(BaseCommand):
    help = ("Create two demo companies with users, projects and issues for demos and performance tests. "
            "Development only: refuses to run when DEBUG is off.")

    def add_arguments(self, parser):
        parser.add_argument("--issues", type=int, default=40, help="issues per project")

    @transaction.atomic
    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError("seed_demo only runs with DJANGO_DEBUG=true.")
        password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12) + "aA1!"
        lines = []
        for company, slug in (("Acme Corp", "acme"), ("Globex", "globex")):
            if Workspace.objects.filter(slug=slug).exists():
                self.stdout.write(f"{company} already exists; skipping.")
                continue
            users = {}
            for role in ("owner", "admin", "project_manager", "member"):
                email = f"{role.replace('_', '')}@{slug}.demo"
                users[role] = User.objects.create_user(email, password, first_name=role.title())
            ws = Workspace.objects.create(name=company, slug=slug, created_by=users["owner"])
            for role, user in users.items():
                Membership.objects.create(workspace=ws, user=user, role=Role(role))
            Subscription.objects.create(workspace=ws, plan="business", status="active")  # demo: no limits in the way
            project = Project.objects.create(workspace=ws, name=f"{company} Website", key=slug[:3].upper() + "W",
                                             description="Demo project", created_by=users["owner"])
            for u in (users["owner"], users["project_manager"], users["member"], users["admin"]):
                ProjectMember.objects.create(workspace=ws, project=project, user=u)
            create_project_defaults(project)
            statuses = list(WorkflowStatus.objects.filter(project=project).order_by("position"))
            sprint = Sprint.objects.create(workspace=ws, project=project, name="Sprint 1", goal="Ship the basics",
                                           start_date="2026-11-02", end_date="2026-11-13", status=SprintStatus.ACTIVE)
            assignees = [users["member"], users["project_manager"], users["owner"], None]
            for n in range(1, opts["issues"] + 1):
                project.issue_counter = n
                issue = Issue.objects.create(
                    workspace=ws, project=project, number=n, title=f"{TITLES[n % len(TITLES)]} #{n}",
                    status=statuses[n % 3], priority=["low", "medium", "high", "urgent"][n % 4],
                    assignee=assignees[n % 4], reporter=users["owner"], position=float(n),
                    sprint=sprint if n % 2 else None, labels=["demo"])
                if n % 5 == 0:
                    Comment.objects.create(workspace=ws, project=project, issue=issue, author=users["member"],
                                           body="Looking into this.")
            project.save(update_fields=["issue_counter"])
            lines.append(f"{company}: " + ", ".join(u.email for u in users.values()))
        if lines:
            self.stdout.write(self.style.SUCCESS("Demo data created. Password for all demo users: " + password))
            for line in lines:
                self.stdout.write(line)

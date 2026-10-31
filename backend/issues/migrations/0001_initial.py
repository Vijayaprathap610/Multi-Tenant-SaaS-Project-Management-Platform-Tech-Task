from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('sprints', '0001_initial'),
        ('workflows', '0001_initial'),
        ('workspaces', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('number', models.PositiveIntegerField(editable=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('labels', models.JSONField(blank=True, default=list)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('position', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='projects.project')),
                ('reporter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('sprint', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issues', to='sprints.sprint')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issues', to='workflows.workflowstatus')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('project', 'number'), name='unique_issue_number'),
                ],
                'indexes': [
                    models.Index(fields=['workspace', 'project', 'status', 'position'], name='issues_issu_workspa_0d5402_idx'),
                    models.Index(fields=['project', 'assignee'], name='issues_issu_project_1d6c8b_idx'),
                    models.Index(fields=['project', 'sprint'], name='issues_issu_project_807185_idx'),
                ],
            },
        ),
    ]


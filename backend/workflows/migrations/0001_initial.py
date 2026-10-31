from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=60)),
                ('category', models.CharField(choices=[('todo', 'To do'), ('in_progress', 'In progress'), ('done', 'Done')], max_length=12)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statuses', to='projects.project')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['position', 'created_at'],
                'constraints': [
                    models.UniqueConstraint(fields=('project', 'name'), name='unique_status_name'),
                ],
            },
        ),
        migrations.CreateModel(
            name='WorkflowTransition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('from_status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing', to='workflows.workflowstatus')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='projects.project')),
                ('to_status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming', to='workflows.workflowstatus')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('from_status', 'to_status'), name='unique_transition'),
                ],
            },
        ),
    ]

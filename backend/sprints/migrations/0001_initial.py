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
            name='Sprint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('goal', models.TextField(blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed')], default='planned', max_length=10)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sprints', to='projects.project')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(condition=models.Q(('status', 'active')), fields=('project',), name='one_active_sprint_per_project'),
                ],
                'indexes': [
                    models.Index(fields=['project', 'status'], name='sprints_spr_project_fa171a_idx'),
                ],
            },
        ),
    ]

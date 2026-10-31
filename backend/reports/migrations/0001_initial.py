from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('workspaces', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('ready', 'Ready'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('error', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='projects.project')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['project', '-created_at'], name='reports_rep_project_b0cfec_idx'),
                ],
            },
        ),
    ]

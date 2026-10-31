from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('issues', '0001_initial'),
        ('workspaces', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(max_length=64)),
                ('message', models.CharField(max_length=300)),
                ('project_id', models.UUIDField(blank=True, null=True)),
                ('dedupe_key', models.CharField(max_length=64)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('issue', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='issues.issue')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('recipient', 'dedupe_key'), name='unique_notification_event'),
                ],
                'indexes': [
                    models.Index(fields=['recipient', 'workspace', 'read_at', '-created_at'], name='notificatio_recipie_f3d53d_idx'),
                ],
            },
        ),
    ]


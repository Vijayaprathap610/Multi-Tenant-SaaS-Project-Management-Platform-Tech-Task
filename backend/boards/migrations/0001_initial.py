from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('workflows', '0001_initial'),
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boards', to='projects.project')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
        ),
        migrations.CreateModel(
            name='BoardColumn',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=60)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='boards.board')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workflows.workflowstatus')),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['position'],
                'constraints': [
                    models.UniqueConstraint(fields=('board', 'status'), name='unique_column_status'),
                ],
            },
        ),
    ]

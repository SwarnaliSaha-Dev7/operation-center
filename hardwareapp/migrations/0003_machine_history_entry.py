# Generated manually for MachineHistoryEntry

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hardwareapp', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineHistoryEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('machine_created', 'Machine created'), ('member_changed', 'Member assignment changed'), ('os_changed', 'Operating system changed'), ('components_updated', 'Hardware configuration updated')], db_index=True, max_length=32)),
                ('summary', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='machine_history_entries', to=settings.AUTH_USER_MODEL)),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history_entries', to='hardwareapp.machinetable')),
            ],
            options={
                'db_table': 'machine_history_entry',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='machinehistoryentry',
            index=models.Index(fields=['machine', 'created_at'], name='machine_his_machine_created_idx'),
        ),
    ]

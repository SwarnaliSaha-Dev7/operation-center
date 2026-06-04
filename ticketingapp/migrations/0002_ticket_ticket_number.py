import django.core.validators
from django.db import migrations, models


def backfill_ticket_numbers(apps, schema_editor):
    Ticket = apps.get_model('ticketingapp', 'Ticket')
    for i, t in enumerate(Ticket.objects.order_by('pk'), start=1):
        Ticket.objects.filter(pk=t.pk).update(ticket_number=f'{i:08d}')


class Migration(migrations.Migration):

    dependencies = [
        ('ticketingapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='ticket_number',
            field=models.CharField(blank=True, editable=False, max_length=8, null=True),
        ),
        migrations.RunPython(backfill_ticket_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='ticket',
            name='ticket_number',
            field=models.CharField(
                db_index=True,
                editable=False,
                max_length=8,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        '^\\d{8}$',
                        'Must be exactly 8 digits',
                    )
                ],
            ),
        ),
    ]

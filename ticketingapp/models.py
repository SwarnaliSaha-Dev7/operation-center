from django.conf import settings
from django.core.validators import RegexValidator
from django.db import IntegrityError, models, transaction
from django.db.models import Max

from commonapp.models import CreatedUpdatedByMixin


class Ticket(CreatedUpdatedByMixin, models.Model):
    """IT helpdesk ticket: raised by a member; IT (manage_it_tickets) takes, moves to in progress, resolves; the raising member closes."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        NORMAL = 'normal', 'Normal'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    all_objects = models.Manager()
    ticket_number = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        db_index=True,
        validators=[RegexValidator(r'^\d{8}$', 'Must be exactly 8 digits')],
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True,
    )
    category = models.CharField(
        max_length=64,
        blank=True,
        help_text='e.g. Software, Access, Network',
    )
    # Reporter is CreatedUpdatedByMixin.createdby
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_assigned',
    )

    class Meta:
        db_table = 'it_ticket'
        verbose_name = 'IT ticket'
        verbose_name_plural = 'IT tickets'
        ordering = ['-created_at']
        permissions = [
            ('manage_it_tickets', 'Can manage IT ticket queue (all tickets, assign, internal notes)'),
        ]
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if self.ticket_number:
            super().save(*args, **kwargs)
            return
        for _ in range(64):
            try:
                with transaction.atomic():
                    m = Ticket.all_objects.aggregate(x=Max('ticket_number'))['x']
                    n = int(m) + 1 if m else 1
                    if n > 99_999_999:
                        raise RuntimeError('Ticket number space exhausted.')
                    self.ticket_number = f'{n:08d}'
                    super().save(*args, **kwargs)
                return
            except IntegrityError:
                self.ticket_number = ''
                continue
        raise RuntimeError('Could not allocate a unique ticket number.')

    def __str__(self):
        if self.ticket_number:
            return f'{self.ticket_number} — {self.title}'
        return self.title


class TicketComment(models.Model):
    """Threaded discussion and feedback; internal notes visible only to IT."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_comments',
    )
    body = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text='If true, only IT team members (manage IT tickets) can see this comment.',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'it_ticket_comment'
        ordering = ['created_at']

    def __str__(self):
        return f'Comment on {self.ticket_id} by {self.author_id}'

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notification for a single recipient."""

    class Category(models.TextChoices):
        GENERAL = 'general', 'General'
        TICKET = 'ticket', 'Ticket'
        MEMBER = 'member', 'Member'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
        help_text='Member who triggered this notification, if any.',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text='Internal path only (e.g. /ticketing/tickets/5/).',
    )
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.GENERAL,
        db_index=True,
    )
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'app_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'read_at', '-created_at']),
        ]

    def __str__(self):
        return f'{self.title} → {self.recipient_id}'

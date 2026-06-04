from django.conf import settings
from django.db import models

from commonapp.models import CreatedUpdatedByMixin
from memberapp.models import Team


class HardwareIssueTable(CreatedUpdatedByMixin, models.Model):
    component_route = models.CharField(max_length=80)
    component_type = models.CharField(max_length=80)
    component_id = models.PositiveIntegerField()
    component_name = models.TextField(blank=True, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='hardware_issues')
    quantity = models.PositiveIntegerField(default=1)
    reason = models.TextField()
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hardware_issues_created',
    )

    class Meta:
        db_table = 'hardware_issue'
        verbose_name = 'hardware issue'
        verbose_name_plural = 'hardware issues'
        indexes = [
            models.Index(fields=['component_type', 'component_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.component_type} #{self.component_id} x{self.quantity}'

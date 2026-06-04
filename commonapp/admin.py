from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.utils.translation import gettext_lazy as _


def _action_label(flag):
    if flag == ADDITION:
        return _('Add')
    if flag == CHANGE:
        return _('Change')
    if flag == DELETION:
        return _('Delete')
    return str(flag)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Read-only view of all actions performed in Django admin (who changed what, when)."""

    date_hierarchy = 'action_time'

    list_display = (
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'action_label',
        'change_message_short',
    )
    list_filter = (
        'action_flag',
        ('content_type', admin.RelatedOnlyFieldListFilter),
        'user',
    )
    search_fields = (
        'object_repr',
        'change_message',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'action_time',
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message',
    )
    list_per_page = 50
    ordering = ('-action_time',)

    fieldsets = (
        (None, {'fields': readonly_fields}),
    )

    @admin.display(description=_('Action'), ordering='action_flag')
    def action_label(self, obj):
        return _action_label(obj.action_flag)

    @admin.display(description=_('Change message'))
    def change_message_short(self, obj):
        msg = (obj.change_message or '').strip()
        if len(msg) > 120:
            msg = msg[:117] + '…'
        return msg or '—'

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('content_type', 'user')
        )

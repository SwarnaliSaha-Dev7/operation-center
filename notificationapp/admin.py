from django.contrib import admin

from notificationapp.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'category', 'read_at', 'created_at')
    list_filter = ('category', 'read_at')
    search_fields = ('title', 'body', 'recipient__username')
    readonly_fields = ('created_at',)
    raw_id_fields = ('recipient', 'actor')

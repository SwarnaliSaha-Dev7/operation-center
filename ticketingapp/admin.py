from django.contrib import admin

from ticketingapp.models import Ticket, TicketComment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('author', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'id', 'title', 'status', 'priority', 'createdby', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('ticket_number', 'title', 'description')
    readonly_fields = ('ticket_number',)
    raw_id_fields = ('assigned_to', 'createdby', 'updatedby')
    inlines = [TicketCommentInline]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal',)

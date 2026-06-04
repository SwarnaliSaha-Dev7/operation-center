from django.contrib import admin

from hardwareissueapp.models import HardwareIssueTable


@admin.register(HardwareIssueTable)
class HardwareIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'component_type', 'component_name', 'quantity', 'team', 'issued_by', 'created_at')
    list_filter = ('component_type', 'team', 'created_at')
    search_fields = ('component_name', 'component_type', 'reason')

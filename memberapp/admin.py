from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Team, Department, Designation, User


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'employee_id', 'team', 'department', 'designation', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'team', 'department', 'designation')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id', 'phone')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')
    autocomplete_fields = ('team', 'department', 'designation')

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('employee_id', 'phone', 'team', 'department', 'designation')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('employee_id', 'phone', 'team', 'department', 'designation')}),
    )

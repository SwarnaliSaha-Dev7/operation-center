from django.db import models
from django.contrib.auth.models import AbstractUser
from commonapp.models import CreatedUpdatedByMixin


class Team(CreatedUpdatedByMixin, models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'member_user_team'
        verbose_name = 'team'
        verbose_name_plural = 'teams'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(CreatedUpdatedByMixin, models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'member_user_department'
        verbose_name = 'department'
        verbose_name_plural = 'departments'
        ordering = ['name']

    def __str__(self):
        return self.name


class Designation(CreatedUpdatedByMixin, models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'member_user_designation'
        verbose_name = 'designation'
        verbose_name_plural = 'designations'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Member fields (employee_id, phone, team, department, designation) are on the User class.
    """
    employee_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    email_password = models.CharField(max_length=64, null=True, blank=True)
    discord_id = models.CharField(max_length=64, null=True, blank=True)
    discord_password = models.CharField(max_length=64, null=True, blank=True)

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )

    class Meta:
        db_table = 'member_user_user'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['username']

    def __str__(self):
        return self.get_full_name() or self.username

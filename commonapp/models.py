from django.db import models
from django.conf import settings
from commonapp.utils import get_current_user


# Create your models here.
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_delete=False)



class CreatedUpdatedByMixin(models.Model):
    """Abstract mixin that adds createdby and updatedby fields, auto-set from current user."""
    createdby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        editable=False,
        verbose_name='Created by',
    )
    updatedby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        editable=False,
        verbose_name='Updated by',
    )
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        try:
            user = get_current_user()
            if user and user.is_authenticated:
                if not self.pk:
                    self.createdby = user
                self.updatedby = user
        except ImportError:
            pass
        super().save(*args, **kwargs)
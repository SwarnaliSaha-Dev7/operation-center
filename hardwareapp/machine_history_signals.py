"""Record machine history for lifecycle and member changes; OS m2m."""
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from hardwareapp.machine_history import (
    log_machine_created,
    log_member_changed,
    log_os_changed,
)
from hardwareapp.models import MachineTable


@receiver(pre_save, sender=MachineTable)
def machine_history_presave(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = MachineTable.objects.get(pk=instance.pk)
            instance._history_prev_member_id = old.member_id
        except MachineTable.DoesNotExist:
            instance._history_prev_member_id = None
    else:
        instance._history_prev_member_id = None


@receiver(post_save, sender=MachineTable)
def machine_history_postsave(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    if created:
        log_machine_created(instance)
        return
    prev = getattr(instance, '_history_prev_member_id', None)
    if prev != instance.member_id:
        log_member_changed(instance, prev, instance.member_id)


@receiver(m2m_changed, sender=MachineTable.operating_system.through)
def machine_history_os_changed(sender, instance, action, pk_set, **kwargs):
    if kwargs.get('raw'):
        return
    if not isinstance(instance, MachineTable):
        return
    if action == 'post_clear':
        log_os_changed(instance, action, set())
    elif action in ('post_add', 'post_remove') and pk_set:
        log_os_changed(instance, action, pk_set)

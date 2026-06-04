"""
Automatically update component assign/remaining when they are assigned to or
removed from a machine (via through model quantity), or when a component's
quantity is updated. assign and remaining are system-managed only (not editable
by users); they stay in sync via these signals.
"""
from django.db.models import F
from django.db.models.functions import Greatest, Least
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from hardwareapp.models import (
    MachineTable,
    ProcessorTable,
    GraphicsCardTable,
    MotherboardTable,
    RAMTable,
    HDDTable,
    SSDTable,
    LiquidCoolerTable,
    UPSTable,
    MonitorTable,
    KeyboardTable,
    MouseTable,
    HeadphoneTable,
    Pentable,
    SpeakerTable,
    WebcamTable,
    PowerSupplyTable,
    CabinetTable,
    MachineProcessorThrough,
    MachineRAMThrough,
    MachineSSDThrough,
    MachineMotherboardThrough,
    MachinePowerSupplyThrough,
    MachineCabinetThrough,
    MachineLiquidCoolerThrough,
    MachineGraphicsCardThrough,
    MachineHDDThrough,
    MachineUPSThrough,
    MachineMonitorThrough,
    MachineKeyboardThrough,
    MachineMouseThrough,
    MachineHeadphoneThrough,
    MachinePentableThrough,
    MachineSpeakerThrough,
    MachineWebcamThrough,
)

# All component models that have quantity, assign, remaining (excludes OperatingSystemTable, MachineTable)
_COMPONENT_MODELS = (
    ProcessorTable, GraphicsCardTable, MotherboardTable, RAMTable, HDDTable, SSDTable,
    LiquidCoolerTable, UPSTable, MonitorTable, KeyboardTable, MouseTable, HeadphoneTable,
    Pentable, SpeakerTable, WebcamTable, PowerSupplyTable, CabinetTable,
)

# (through_model, component_fk_field_name, component_model)
_THROUGH_CONFIG = (
    (MachineProcessorThrough, "processor", ProcessorTable),
    (MachineRAMThrough, "ram", RAMTable),
    (MachineSSDThrough, "ssd", SSDTable),
    (MachineMotherboardThrough, "motherboard", MotherboardTable),
    (MachinePowerSupplyThrough, "power_supply", PowerSupplyTable),
    (MachineCabinetThrough, "cabinet", CabinetTable),
    (MachineLiquidCoolerThrough, "liquid_cooler", LiquidCoolerTable),
    (MachineGraphicsCardThrough, "graphics_card", GraphicsCardTable),
    (MachineHDDThrough, "hdd", HDDTable),
    (MachineUPSThrough, "ups", UPSTable),
    (MachineMonitorThrough, "monitor", MonitorTable),
    (MachineKeyboardThrough, "keyboard", KeyboardTable),
    (MachineMouseThrough, "mouse", MouseTable),
    (MachineHeadphoneThrough, "headphone", HeadphoneTable),
    (MachinePentableThrough, "pentable", Pentable),
    (MachineSpeakerThrough, "speaker", SpeakerTable),
    (MachineWebcamThrough, "webcam", WebcamTable),
)


def _sync_assign_remaining_on_save(instance):
    """When quantity (or assign) changes on save, cap assign in [0, quantity] so assign and remaining are never negative."""
    if not hasattr(instance, "quantity") or not hasattr(instance, "assign") or not hasattr(instance, "remaining"):
        return
    quantity = max(0, instance.quantity or 0)
    assign = instance.assign or 0
    instance.assign = max(0, min(assign, quantity))
    instance.remaining = max(0, quantity - instance.assign)


def _update_component_assign_remaining(component_model, pk_set, delta):
    """Apply delta to assign; cap assign in [0, quantity] so assign and remaining are never negative."""
    if not pk_set:
        return
    # assign must be in [0, quantity] so remaining = quantity - assign is never negative
    new_assign = Least(F("quantity"), Greatest(0, F("assign") + delta))
    component_model.objects.filter(pk__in=pk_set).update(
        assign=new_assign,
        remaining=F("quantity") - new_assign,
    )


@receiver(pre_save)
def component_sync_assign_remaining(sender, instance, **kwargs):
    """
    When a component's quantity (or assign) is updated, keep remaining = quantity - assign
    and ensure assign does not exceed quantity.
    """
    if sender not in _COMPONENT_MODELS:
        return
    _sync_assign_remaining_on_save(instance)


def _through_post_save(sender, instance, created, **kwargs):
    """When a through row is saved, update component assign/remaining by instance.quantity."""
    for through_cls, fk_name, component_model in _THROUGH_CONFIG:
        if sender is through_cls:
            pk = getattr(instance, fk_name + "_id", None) or getattr(instance, fk_name).pk
            qty = instance.quantity or 0
            if created:
                _update_component_assign_remaining(component_model, [pk], qty)
            else:
                old_qty = getattr(instance, "_old_quantity", 0)
                _update_component_assign_remaining(component_model, [pk], qty - old_qty)
            return


def _through_pre_save(sender, instance, **kwargs):
    """Store old quantity for through model update."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_quantity = old.quantity or 0
        except sender.DoesNotExist:
            instance._old_quantity = 0
    else:
        instance._old_quantity = 0


def _through_post_delete(sender, instance, **kwargs):
    """When a through row is deleted, decrement component assign by instance.quantity."""
    for through_cls, fk_name, component_model in _THROUGH_CONFIG:
        if sender is through_cls:
            pk = getattr(instance, fk_name + "_id", None) or (getattr(instance, fk_name).pk if getattr(instance, fk_name, None) else None)
            if pk is not None:
                qty = -(instance.quantity or 0)
                _update_component_assign_remaining(component_model, [pk], qty)
            return


for _through_cls, _, _ in _THROUGH_CONFIG:
    pre_save.connect(_through_pre_save, sender=_through_cls)
    post_save.connect(_through_post_save, sender=_through_cls)
    post_delete.connect(_through_post_delete, sender=_through_cls)

from django.conf import settings
from django.db import models
from commonapp.models import CreatedUpdatedByMixin
from memberapp.models import Team , Department

# Create your models here.
class OperatingSystemTable(CreatedUpdatedByMixin, models.Model):
    name = models.TextField(null=True, blank=True)
    version = models.TextField(null=True, blank=True)

    class Meta:
        db_table  = 'operating_system'
        verbose_name = 'operating_system'
        verbose_name_plural = verbose_name + 's'

    def __str__(self):
        return self.name

class ProcessorTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='processor_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    architecture = models.TextField(null=True, blank=True)
    cores = models.IntegerField(default=0)
    threads = models.IntegerField(default=0)
    frequency = models.TextField(null=True, blank=True)
    cache = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'processor'
        verbose_name = 'processor'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name


class GraphicsCardTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='graphicscard_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    memory = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'graphics_card'
        verbose_name = 'graphics_card'
        verbose_name_plural = verbose_name + 's'

    def __str__(self):
        return self.name


class MotherboardTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='motherboard_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    socket = models.TextField(null=True, blank=True)
    memory_slots = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'motherboard'
        verbose_name = 'motherboard'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name


class RAMTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='ram_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    memory = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'ram'
        verbose_name = 'ram'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class HDDTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='hdd_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    capacity = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'hdd'
        verbose_name = 'hdd'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class SSDTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='ssd_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    capacity = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'ssd'
        verbose_name = 'ssd'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class LiquidCoolerTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='liquidcooler_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)
    is_liquid = models.BooleanField(default=False)

    class Meta:
        db_table  = 'liquid_cooler'
        verbose_name = 'liquid_cooler'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class UPSTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='ups_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'ups'
        verbose_name = 'ups'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name
    
class MonitorTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='monitor_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'monitor'
        verbose_name = 'monitor'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class KeyboardTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='keyboard_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'keyboard'
        verbose_name = 'keyboard'
        verbose_name_plural = verbose_name + 's'

    def __str__(self):
        return self.name
    
class MouseTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='mouse_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'mouse'
        verbose_name = 'mouse'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class HeadphoneTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='headphone_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'headphone'
        verbose_name = 'headphone'
        verbose_name_plural = verbose_name + 's'    

    def __str__(self):
        return self.name

class Pentable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='pentable_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'pentable'
        verbose_name = 'pentable'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class SpeakerTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='speaker_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'speaker'
        verbose_name = 'speaker'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name

class WebcamTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='webcam_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'webcam'
        verbose_name = 'webcam'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name


class PowerSupplyTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='powersupply_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'power_supply'
        verbose_name = 'power_supply'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name



class CabinetTable(CreatedUpdatedByMixin, models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='cabinet_records')
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    model = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    assign = models.IntegerField(default=0)
    remaining = models.IntegerField(default=0)
    issue = models.IntegerField(default=0)

    class Meta:
        db_table  = 'cabinet'
        verbose_name = 'cabinet'
        verbose_name_plural = verbose_name + 's'
        constraints = [
            models.CheckConstraint(condition=models.Q(assign__gte=0), name='%(app_label)s_%(class)s_assign_non_neg'),
            models.CheckConstraint(condition=models.Q(remaining__gte=0), name='%(app_label)s_%(class)s_remaining_non_neg'),
        ]

    def __str__(self):
        return self.name


# Through models for MachineTable M2M with quantity (same component can be assigned with quantity > 1)
class MachineProcessorThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    processor = models.ForeignKey(ProcessorTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_processor_through'


class MachineRAMThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    ram = models.ForeignKey(RAMTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_ram_through'


class MachineSSDThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    ssd = models.ForeignKey(SSDTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_ssd_through'


class MachineMotherboardThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    motherboard = models.ForeignKey(MotherboardTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_motherboard_through'


class MachinePowerSupplyThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    power_supply = models.ForeignKey(PowerSupplyTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_powersupply_through'


class MachineCabinetThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    cabinet = models.ForeignKey(CabinetTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_cabinet_through'


class MachineLiquidCoolerThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    liquid_cooler = models.ForeignKey(LiquidCoolerTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_liquidcooler_through'


class MachineGraphicsCardThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    graphics_card = models.ForeignKey(GraphicsCardTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_graphicscard_through'


class MachineHDDThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    hdd = models.ForeignKey(HDDTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_hdd_through'


class MachineUPSThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    ups = models.ForeignKey(UPSTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_ups_through'


class MachineMonitorThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    monitor = models.ForeignKey(MonitorTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_monitor_through'


class MachineKeyboardThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    keyboard = models.ForeignKey(KeyboardTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_keyboard_through'


class MachineMouseThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    mouse = models.ForeignKey(MouseTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_mouse_through'
        unique_together = (('machine', 'mouse'),)


class MachineHeadphoneThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    headphone = models.ForeignKey(HeadphoneTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_headphone_through'


class MachinePentableThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    pentable = models.ForeignKey(Pentable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_pentable_through'
        unique_together = (('machine', 'pentable'),)


class MachineSpeakerThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    speaker = models.ForeignKey(SpeakerTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_speaker_through'


class MachineWebcamThrough(models.Model):
    machine = models.ForeignKey('MachineTable', on_delete=models.CASCADE)
    webcam = models.ForeignKey(WebcamTable, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'machine_webcam_through'


class MachineTable(CreatedUpdatedByMixin, models.Model):
    
    name = models.TextField(null=True, blank=True)
    code = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False, blank=False, related_name='machines')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=False, blank=False, related_name='machines')

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_machines',
    )

    graphics_card = models.ManyToManyField(GraphicsCardTable, blank=True, related_name='machines', through='MachineGraphicsCardThrough')
    hdd = models.ManyToManyField(HDDTable, blank=True, related_name='machines', through='MachineHDDThrough')
    ups = models.ManyToManyField(UPSTable, blank=True, related_name='machines', through='MachineUPSThrough')
    monitor = models.ManyToManyField(MonitorTable, blank=True, related_name='machines', through='MachineMonitorThrough')
    keyboard = models.ManyToManyField(KeyboardTable, blank=True, related_name='machines', through='MachineKeyboardThrough')
    mouse = models.ManyToManyField(MouseTable, blank=True, related_name='machines', through='MachineMouseThrough')
    headphone = models.ManyToManyField(HeadphoneTable, blank=True, related_name='machines', through='MachineHeadphoneThrough')
    pentable = models.ManyToManyField(Pentable, blank=True, related_name='machines', through='MachinePentableThrough')
    speaker = models.ManyToManyField(SpeakerTable, blank=True, related_name='machines', through='MachineSpeakerThrough')
    webcam = models.ManyToManyField(WebcamTable, blank=True, related_name='machines', through='MachineWebcamThrough')

    operating_system = models.ManyToManyField(OperatingSystemTable, blank=False, related_name='machines')
    processor = models.ManyToManyField(ProcessorTable, blank=False, related_name='machines', through='MachineProcessorThrough')
    ram = models.ManyToManyField(RAMTable, blank=False, related_name='machines', through='MachineRAMThrough')
    ssd = models.ManyToManyField(SSDTable, blank=False, related_name='machines', through='MachineSSDThrough')
    motherboard = models.ManyToManyField(MotherboardTable, blank=False, related_name='machines', through='MachineMotherboardThrough')
    power_supply = models.ManyToManyField(PowerSupplyTable, blank=False, related_name='machines', through='MachinePowerSupplyThrough')
    cabinet = models.ManyToManyField(CabinetTable, blank=False, related_name='machines', through='MachineCabinetThrough')
    liquid_cooler = models.ManyToManyField(LiquidCoolerTable, blank=False, related_name='machines', through='MachineLiquidCoolerThrough')


    class Meta:
        db_table  = 'machine'
        verbose_name = 'machine'
        verbose_name_plural = verbose_name + 's'

    def get_processor_quantities(self):
        return [(t.processor, t.quantity) for t in MachineProcessorThrough.objects.filter(machine=self).select_related('processor')]

    def get_ram_quantities(self):
        return [(t.ram, t.quantity) for t in MachineRAMThrough.objects.filter(machine=self).select_related('ram')]

    def get_ssd_quantities(self):
        return [(t.ssd, t.quantity) for t in MachineSSDThrough.objects.filter(machine=self).select_related('ssd')]

    def get_motherboard_quantities(self):
        return [(t.motherboard, t.quantity) for t in MachineMotherboardThrough.objects.filter(machine=self).select_related('motherboard')]

    def get_power_supply_quantities(self):
        return [(t.power_supply, t.quantity) for t in MachinePowerSupplyThrough.objects.filter(machine=self).select_related('power_supply')]

    def get_cabinet_quantities(self):
        return [(t.cabinet, t.quantity) for t in MachineCabinetThrough.objects.filter(machine=self).select_related('cabinet')]

    def get_liquid_cooler_quantities(self):
        return [(t.liquid_cooler, t.quantity) for t in MachineLiquidCoolerThrough.objects.filter(machine=self).select_related('liquid_cooler')]

    def get_graphics_card_quantities(self):
        return [(t.graphics_card, t.quantity) for t in MachineGraphicsCardThrough.objects.filter(machine=self).select_related('graphics_card')]

    def get_hdd_quantities(self):
        return [(t.hdd, t.quantity) for t in MachineHDDThrough.objects.filter(machine=self).select_related('hdd')]

    def get_ups_quantities(self):
        return [(t.ups, t.quantity) for t in MachineUPSThrough.objects.filter(machine=self).select_related('ups')]

    def get_monitor_quantities(self):
        return [(t.monitor, t.quantity) for t in MachineMonitorThrough.objects.filter(machine=self).select_related('monitor')]

    def get_keyboard_quantities(self):
        return [(t.keyboard, t.quantity) for t in MachineKeyboardThrough.objects.filter(machine=self).select_related('keyboard')]

    def get_mouse_quantities(self):
        return [(t.mouse, t.quantity) for t in MachineMouseThrough.objects.filter(machine=self).select_related('mouse')]

    def get_headphone_quantities(self):
        return [(t.headphone, t.quantity) for t in MachineHeadphoneThrough.objects.filter(machine=self).select_related('headphone')]

    def get_pentable_quantities(self):
        return [(t.pentable, t.quantity) for t in MachinePentableThrough.objects.filter(machine=self).select_related('pentable')]

    def get_speaker_quantities(self):
        return [(t.speaker, t.quantity) for t in MachineSpeakerThrough.objects.filter(machine=self).select_related('speaker')]

    def get_webcam_quantities(self):
        return [(t.webcam, t.quantity) for t in MachineWebcamThrough.objects.filter(machine=self).select_related('webcam')]

    def __str__(self):
        return self.name


class MachineHistoryEntry(models.Model):
    """Append-only audit trail for machine lifecycle, assignments, OS, and hardware configuration."""

    class EventType(models.TextChoices):
        MACHINE_CREATED = 'machine_created', 'Machine created'
        MEMBER_CHANGED = 'member_changed', 'Member assignment changed'
        OS_CHANGED = 'os_changed', 'Operating system changed'
        COMPONENTS_UPDATED = 'components_updated', 'Hardware configuration updated'

    machine = models.ForeignKey(
        MachineTable,
        on_delete=models.CASCADE,
        related_name='history_entries',
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    summary = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='machine_history_entries',
    )

    class Meta:
        db_table = 'machine_history_entry'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['machine', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_event_type_display()} @ {self.created_at}'
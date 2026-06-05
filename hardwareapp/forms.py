from django import forms
from django.db.models import Q
from hardwareapp.models import (
    MachineTable,
    OperatingSystemTable,
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
)

INPUT_CLASS = 'w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'


def validate_quantity_not_below_used(instance, quantity):
    if not instance or not instance.pk:
        return quantity

    used_count = (instance.assign or 0) + (instance.issue or 0)
    if quantity is not None and quantity < used_count:
        raise forms.ValidationError(
            f'Quantity cannot be less than assign + issue count ({used_count}).'
        )
    return quantity


def _component_select_label(obj):
    """
    Format for select options: name-brand-team name-quantity [memory/capacity if present].
    Used by MachineForm and any form showing hardware components in a dropdown.
    """
    if obj is None:
        return ''
    # OperatingSystemTable: no team, no quantity; use name-version
    if hasattr(obj, 'version') and not hasattr(obj, 'quantity'):
        name = (getattr(obj, 'name', None) or '').strip() or '—'
        version = (getattr(obj, 'version', None) or '').strip() or '—'
        return f'{name}-{version}'
    # Team: just name
    if not hasattr(obj, 'brand'):
        return (getattr(obj, 'name', None) or str(obj)).strip() or '—'
    # Hardware components: name-brand-team name-quantity [memory/capacity]
    name = (getattr(obj, 'name', None) or '').strip() or '—'
    brand = (getattr(obj, 'brand', None) or '').strip() or '—'
    team_name = '—'
    if getattr(obj, 'team', None):
        team_name = (getattr(obj.team, 'name', None) or '').strip() or '—'
    quantity = getattr(obj, 'quantity', None)
    if quantity is None:
        quantity = '—'
    parts = [name, brand, team_name]
    if hasattr(obj, 'memory') and getattr(obj, 'memory', None) is not None and obj.memory != 0:
        parts.append(f'{obj.memory}GB')
    if hasattr(obj, 'capacity') and getattr(obj, 'capacity', None) is not None and obj.capacity != 0:
        parts.append(f'{obj.capacity}GB')
    return '-'.join(parts)


class OperatingSystemForm(forms.ModelForm):
    class Meta:
        model = OperatingSystemTable
        fields = ['name', 'version']
        labels = {'name': 'Name', 'version': 'Version'}
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'version': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }
        help_texts = {
            'name': 'Enter the name of the operating system',
            'version': 'Enter the version of the operating system',
        }
        error_messages = {
            'name': {'max_length': 'The name must be less than 255 characters'},
            'version': {'max_length': 'The version must be less than 255 characters'},
        }
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name
    def clean_version(self):
        version = self.cleaned_data.get('version')
        if version and len(version) < 1:
            raise forms.ValidationError('The version must be at least 1 character')
        return version

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'Name'
        self.fields['version'].widget.attrs['placeholder'] = 'Version'
        

class ProcessorForm(forms.ModelForm):
    class Meta:
        model = ProcessorTable
        fields = ['team', 'name', 'brand', 'model', 'architecture', 'cores', 'threads', 'frequency', 'cache', 'quantity']
        labels = {
            'team': 'Team',
            'name': 'Name',
            'brand': 'Brand',
            'model': 'Model',
            'architecture': 'Architecture',
            'cores': 'Cores',
            'threads': 'Threads',
            'frequency': 'Frequency',
            'cache': 'Cache',
            'quantity': 'Quantity',
        }
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'architecture': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'cores': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'threads': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'frequency': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'cache': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the processor',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'architecture': 'Enter the architecture of the processor',
            'cores': 'Enter the number of cores',
            'threads': 'Enter the number of threads',
            'frequency': 'Enter the frequency',
            'cache': 'Enter the cache',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'name': {'max_length': 'The name must be less than 255 characters'},
            'architecture': {'max_length': 'The architecture must be less than 255 characters'},
            'cores': {'min_value': 'The number of cores must be greater than 0'},
            'threads': {'min_value': 'The number of threads must be greater than 0'},
            'frequency': {'max_length': 'The frequency must be less than 255 characters'},
            'cache': {'max_length': 'The cache must be less than 255 characters'},
            'quantity': {'min_value': 'The quantity must be greater than 0'},
        }
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name
    def clean_architecture(self):
        architecture = self.cleaned_data.get('architecture')
        if architecture and len(architecture) < 3:
            raise forms.ValidationError('The architecture must be at least 3 characters')
        return architecture
    def clean_cores(self):
        cores = self.cleaned_data.get('cores')
        if cores and cores < 0:
            raise forms.ValidationError('The number of cores must be greater than 0')
        return cores
    def clean_threads(self):
        threads = self.cleaned_data.get('threads')
        if threads and threads < 0:
            raise forms.ValidationError('The number of threads must be greater than 0')
        return threads
    def clean_frequency(self):
        frequency = self.cleaned_data.get('frequency')
        if frequency and len(frequency) < 3:
            raise forms.ValidationError('The frequency must be at least 3 characters')
        return frequency
    def clean_cache(self):
        cache = self.cleaned_data.get('cache')
        if cache and len(cache) < 3:
            raise forms.ValidationError('The cache must be at least 3 characters')
        return cache
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity < 0:
            raise forms.ValidationError('The quantity must be greater than 0')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'Name'
        self.fields['brand'].widget.attrs['placeholder'] = 'Brand'
        self.fields['model'].widget.attrs['placeholder'] = 'Model'
        self.fields['architecture'].widget.attrs['placeholder'] = 'Architecture'
        self.fields['cores'].widget.attrs['placeholder'] = 'Cores'
        self.fields['threads'].widget.attrs['placeholder'] = 'Threads'
        self.fields['frequency'].widget.attrs['placeholder'] = 'Frequency'
        self.fields['cache'].widget.attrs['placeholder'] = 'Cache'
        self.fields['quantity'].widget.attrs['placeholder'] = 'Quantity'


class GraphicsCardForm(forms.ModelForm):
    class Meta:
        model = GraphicsCardTable
        fields = ['team', 'name', 'brand', 'model', 'memory', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'memory': 'Memory (GB)', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'memory': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'name': 'Enter the name of the graphics card',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'memory': 'Enter memory size in GB',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'memory': {'min_value': 'Memory must be 0 or greater'},
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_memory(self):
        memory = self.cleaned_data.get('memory')
        if memory is not None and memory < 0:
            raise forms.ValidationError('Memory must be 0 or greater')
        return memory

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class MotherboardForm(forms.ModelForm):
    class Meta:
        model = MotherboardTable
        fields = ['team', 'name', 'brand', 'model', 'socket', 'memory_slots', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'socket': 'Socket', 'memory_slots': 'Memory Slots', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'socket': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'memory_slots': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'name': 'Enter the name of the motherboard',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'socket': 'Enter the CPU socket type',
            'memory_slots': 'Enter the number of memory slots',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'memory_slots': {'min_value': 'Memory slots must be 0 or greater'},
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_memory_slots(self):
        value = self.cleaned_data.get('memory_slots')
        if value is not None and value < 0:
            raise forms.ValidationError('Memory slots must be 0 or greater')
        return value

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class RAMForm(forms.ModelForm):
    class Meta:
        model = RAMTable
        fields = ['team', 'name', 'brand', 'model', 'memory', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'memory': 'Memory (GB)', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'memory': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the RAM module',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'memory': 'Enter memory size in GB',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'memory': {'min_value': 'Memory must be 0 or greater'},
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_memory(self):
        memory = self.cleaned_data.get('memory')
        if memory is not None and memory < 0:
            raise forms.ValidationError('Memory must be 0 or greater')
        return memory

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class HDForm(forms.ModelForm):
    class Meta:
        model = HDDTable
        fields = ['team', 'name', 'brand', 'model', 'capacity', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'capacity': 'Capacity (GB)', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'capacity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the HDD',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'capacity': 'Enter capacity in GB',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'capacity': {'min_value': 'Capacity must be 0 or greater'},
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_capacity(self):
        value = self.cleaned_data.get('capacity')
        if value is not None and value < 0:
            raise forms.ValidationError('Capacity must be 0 or greater')
        return value

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class SSDForm(forms.ModelForm):
    class Meta:
        model = SSDTable
        fields = ['team', 'name', 'brand', 'model', 'capacity', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'capacity': 'Capacity (GB)', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'capacity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the SSD',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'capacity': 'Enter capacity in GB',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'capacity': {'min_value': 'Capacity must be 0 or greater'},
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_capacity(self):
        value = self.cleaned_data.get('capacity')
        if value is not None and value < 0:
            raise forms.ValidationError('Capacity must be 0 or greater')
        return value

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class LiquidCoolerForm(forms.ModelForm):
    class Meta:
        model = LiquidCoolerTable
        fields = ['team', 'name', 'brand', 'model', 'quantity', 'is_liquid']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity', 'is_liquid': 'Is Liquid'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'is_liquid': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300'}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the cooler',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
            'is_liquid': 'Check if this is a liquid cooler',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['name', 'brand', 'model', 'quantity']:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class UPSForm(forms.ModelForm):
    class Meta:
        model = UPSTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the UPS',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class MonitorForm(forms.ModelForm):
    class Meta:
        model = MonitorTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the monitor',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class KeyboardForm(forms.ModelForm):
    class Meta:
        model = KeyboardTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the keyboard',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class MouseForm(forms.ModelForm):
    class Meta:
        model = MouseTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the mouse',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class HeadphoneForm(forms.ModelForm):
    class Meta:
        model = HeadphoneTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the headphone',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class PentableForm(forms.ModelForm):
    class Meta:
        model = Pentable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the pen tablet',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class SpeakerForm(forms.ModelForm):
    class Meta:
        model = SpeakerTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the speaker',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class WebcamForm(forms.ModelForm):
    class Meta:
        model = WebcamTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the webcam',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class PowerSupplyForm(forms.ModelForm):
    class Meta:
        model = PowerSupplyTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the power supply',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class CabinetForm(forms.ModelForm):
    class Meta:
        model = CabinetTable
        fields = ['team', 'name', 'brand', 'model', 'quantity']
        labels = {'team': 'Team', 'name': 'Name', 'brand': 'Brand', 'model': 'Model', 'quantity': 'Quantity'}
        widgets = {
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'brand': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'model': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }
        help_texts = {
            'team': 'Required. Select the team.',
            'name': 'Enter the name of the cabinet/chassis',
            'brand': 'Enter the brand',
            'model': 'Enter the model',
            'quantity': 'Enter the quantity',
        }
        error_messages = {
            'quantity': {'min_value': 'Quantity must be 0 or greater'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('The name must be at least 3 characters')
        return name

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if brand and len(brand) < 3:
            raise forms.ValidationError('The brand must be at least 3 characters')
        return brand

    def clean_model(self):
        model = self.cleaned_data.get('model')
        if model and len(model) < 3:
            raise forms.ValidationError('The model must be at least 3 characters')
        return model

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError('Quantity must be 0 or greater')
        return validate_quantity_not_below_used(self.instance, quantity)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.Meta.fields:
            self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]


class MachineForm(forms.ModelForm):
    """Basic machine fields + hidden JSON fields for component rows (id + qty). UI built by JS/API."""

    # Component types with through-model; JS sends JSON array of {id, qty} per type
    COMPONENT_ENTRY_FIELDS = [
        'processor', 'ram', 'ssd', 'motherboard', 'power_supply', 'cabinet', 'liquid_cooler',
        'graphics_card', 'hdd', 'ups', 'monitor', 'keyboard', 'mouse',
        'headphone', 'pentable', 'speaker', 'webcam',
    ]
    REQUIRED_COMPONENT_FIELDS = [
        'processor', 'ram', 'ssd', 'motherboard', 'power_supply', 'cabinet', 'liquid_cooler',
    ]
    COMPONENT_MODEL_MAP = {
        'processor': ProcessorTable, 'ram': RAMTable, 'ssd': SSDTable,
        'motherboard': MotherboardTable, 'power_supply': PowerSupplyTable,
        'cabinet': CabinetTable, 'liquid_cooler': LiquidCoolerTable,
        'graphics_card': GraphicsCardTable, 'hdd': HDDTable, 'ups': UPSTable,
        'monitor': MonitorTable, 'keyboard': KeyboardTable, 'mouse': MouseTable,
        'headphone': HeadphoneTable, 'pentable': Pentable, 'speaker': SpeakerTable,
        'webcam': WebcamTable,
    }

    class Meta:
        model = MachineTable
        fields = [
            'name', 'code', 'operating_system', 'description', 'team','department', 'member', 
        ]
        labels = {
            'name': 'Name',
            'code': 'Code',
            'operating_system': 'Operating System',
            'description': 'Description',
            'team': 'Team',
            'department':'Department',
            'member': 'Member',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'team': forms.Select(attrs={'class': INPUT_CLASS + ' select2-field'}),
            'department':forms.Select(attrs={'class': INPUT_CLASS + ' select2-field'}),
            'member': forms.Select(attrs={'class': INPUT_CLASS + ' select2-field'}),
            'operating_system': forms.SelectMultiple(attrs={'class': INPUT_CLASS + ' select2-field'}),
        }
        help_texts = {
            'name': 'A short name for this machine (e.g. Workstation-01).',
            'code': 'Optional unique code or asset ID for the machine.',
            'description': 'Optional notes or description of the machine configuration.',
            'department':'Required. Select the department this machine is assigned to.',
            'team': 'Required. Select the team this machine is assigned to.',
            'member': 'Optional. Select the member (user) this machine is assigned to.',
            'operating_system': 'Required. Select one or more OS installed on this machine.',
        }
        error_messages = {
            'name': {'required': 'Machine name is required for identification.'},
            'team': {'required': 'Please select a team.'},
            'department':{'required': 'Please select a department.'},
            'operating_system': {'required': 'Please select an operating system.'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        if name and len(name) > 500:
            raise forms.ValidationError('Name must be 500 characters or less.')
        return (name or '').strip() or None

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and len(code.strip()) < 1:
            return None
        if code and len(code) > 64:
            raise forms.ValidationError('Code must be 64 characters or less.')
        return (code or '').strip() or None

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description) > 2000:
            raise forms.ValidationError('Description must be 2000 characters or less.')
        return (description or '').strip() or None

    def clean(self):
        import json
        cleaned = super().clean()
        for field_name in self.COMPONENT_ENTRY_FIELDS:
            raw = self.data.get(field_name + '_entries') or self.initial.get(field_name + '_entries') or '[]'
            try:
                entries = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, ValueError):
                entries = []
            if not isinstance(entries, list):
                entries = []
            out = []
            for e in entries:
                comp_id = e.get('id') if isinstance(e, dict) else None
                try:
                    comp_id = int(comp_id) if comp_id is not None else None
                except (TypeError, ValueError):
                    comp_id = None
                qty = e.get('qty', 1) if isinstance(e, dict) else 1
                try:
                    qty = max(1, int(qty))
                except (TypeError, ValueError):
                    qty = 1
                if comp_id:
                    out.append({'id': comp_id, 'qty': qty})
            cleaned[field_name + '_entries'] = out
            if field_name in self.REQUIRED_COMPONENT_FIELDS and len(out) == 0:
                self.add_error(
                    field_name + '_entries',
                    forms.ValidationError('Add at least one item.', code='required'),
                )
            model_class = self.COMPONENT_MODEL_MAP.get(field_name)
            if model_class and out:
                from collections import defaultdict
                by_id = defaultdict(int)
                for e in out:
                    by_id[e['id']] += e['qty']
                for comp_id, total_qty in by_id.items():
                    try:
                        comp = model_class.objects.get(pk=comp_id)
                        if total_qty > comp.quantity:
                            self.add_error(
                                field_name + '_entries',
                                forms.ValidationError(
                                    'Total quantity for one or more items exceeds available (%s has %s total).' % (
                                        getattr(comp, 'name', comp_id), comp.quantity
                                    ),
                                    code='over_quantity',
                                ),
                            )
                            break
                    except model_class.DoesNotExist:
                        self.add_error(
                            field_name + '_entries',
                            forms.ValidationError('Invalid component selected.', code='invalid'),
                        )
                        break
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        for f in self.Meta.fields:
            if f in self.Meta.labels:
                self.fields[f].widget.attrs['placeholder'] = self.Meta.labels[f]
        if 'team' in self.fields:
            self.fields['team'].empty_label = 'Select team…'
        if 'member' in self.fields:
            self.fields['member'].empty_label = 'Select member…'
            self.fields['member'].label_from_instance = lambda u: u.get_full_name() or u.username
        if 'operating_system' in self.fields:
            self.fields['operating_system'].label_from_instance = _component_select_label
        # Hidden fields for JS-populated component entries (JSON)
        for field_name in self.COMPONENT_ENTRY_FIELDS:
            self.fields[field_name + '_entries'] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(attrs={'data-component-type': field_name}),
            )
        from collections import OrderedDict
        order = list(self.fields.keys())
        self.fields = OrderedDict((k, self.fields[k]) for k in order)



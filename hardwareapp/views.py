from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)

from commonapp.global_filters import apply_inventory_assignee_scope, apply_inventory_date_range, apply_machine_filters
from commonapp.mixin import AutoPermissionRequiredMixin
from commonapp.utils import get_datatables_params
from hardwareapp.list_summary import (
    apply_team_filter,
    inventory_list_extras,
    machine_list_extras,
    os_list_extras,
)
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
    MachineHistoryEntry,
)

from hardwareapp.forms import (
    MachineForm,
    OperatingSystemForm,
    ProcessorForm,
    GraphicsCardForm,
    MotherboardForm,
    RAMForm,
    HDForm,
    SSDForm,
    LiquidCoolerForm,
    UPSForm,
    MonitorForm,
    KeyboardForm,
    MouseForm,
    HeadphoneForm,
    PentableForm,
    SpeakerForm,
    WebcamForm,
    PowerSupplyForm,
    CabinetForm,
)
from hardwareissueapp.models import HardwareIssueTable


def _issue_totals_for_component(component_type, page):
    ids = [obj.pk for obj in page]
    if not ids:
        return {}
    rows = (
        HardwareIssueTable.objects.filter(
            is_delete=False,
            component_type=component_type,
            component_id__in=ids,
        )
        .values('component_id')
        .annotate(total=Sum('quantity'))
    )
    return {row['component_id']: row['total'] for row in rows}


def _inventory_table_team_name(obj):
    """Team column cell for hardware inventory DataTables."""
    t = getattr(obj, 'team', None)
    return (getattr(t, 'name', None) or '').strip() or '—'


# (field_name, through_model, through_fk_attr) for saving machine component quantities
_MACHINE_THROUGH_SAVE = (
    ('processor', MachineProcessorThrough, 'processor'),
    ('ram', MachineRAMThrough, 'ram'),
    ('ssd', MachineSSDThrough, 'ssd'),
    ('motherboard', MachineMotherboardThrough, 'motherboard'),
    ('power_supply', MachinePowerSupplyThrough, 'power_supply'),
    ('cabinet', MachineCabinetThrough, 'cabinet'),
    ('liquid_cooler', MachineLiquidCoolerThrough, 'liquid_cooler'),
    ('graphics_card', MachineGraphicsCardThrough, 'graphics_card'),
    ('hdd', MachineHDDThrough, 'hdd'),
    ('ups', MachineUPSThrough, 'ups'),
    ('monitor', MachineMonitorThrough, 'monitor'),
    ('keyboard', MachineKeyboardThrough, 'keyboard'),
    ('mouse', MachineMouseThrough, 'mouse'),
    ('headphone', MachineHeadphoneThrough, 'headphone'),
    ('pentable', MachinePentableThrough, 'pentable'),
    ('speaker', MachineSpeakerThrough, 'speaker'),
    ('webcam', MachineWebcamThrough, 'webcam'),
)


def _component_option_label(obj):
    """Format for API dropdown: same as form label."""
    if obj is None:
        return '—'
    if hasattr(obj, 'version') and not hasattr(obj, 'quantity'):
        return f'{getattr(obj, "name", "") or "—"}-{getattr(obj, "version", "") or "—"}'
    if not hasattr(obj, 'brand'):
        return (getattr(obj, 'name', None) or str(obj)).strip() or '—'
    name = (getattr(obj, 'name', None) or '').strip() or '—'
    brand = (getattr(obj, 'brand', None) or '').strip() or '—'
    team_name = (getattr(obj.team, 'name', None) or '—').strip() if getattr(obj, 'team', None) else '—'
    parts = [name, brand, team_name]
    if getattr(obj, 'memory', None):
        parts.append(f'{obj.memory}GB')
    if getattr(obj, 'capacity', None):
        parts.append(f'{obj.capacity}GB')
    return '-'.join(parts)


def _inventory_table_team_name(obj):
    """Team column cell for hardware inventory DataTables."""
    t = getattr(obj, 'team', None)
    return (getattr(t, 'name', None) or '').strip() or '—'


# Component model and FK attr for API options (model, fk_attr for through)
_COMPONENT_OPTIONS_CONFIG = (
    ('processor', ProcessorTable, 'processor'),
    ('ram', RAMTable, 'ram'),
    ('ssd', SSDTable, 'ssd'),
    ('motherboard', MotherboardTable, 'motherboard'),
    ('power_supply', PowerSupplyTable, 'power_supply'),
    ('cabinet', CabinetTable, 'cabinet'),
    ('liquid_cooler', LiquidCoolerTable, 'liquid_cooler'),
    ('graphics_card', GraphicsCardTable, 'graphics_card'),
    ('hdd', HDDTable, 'hdd'),
    ('ups', UPSTable, 'ups'),
    ('monitor', MonitorTable, 'monitor'),
    ('keyboard', KeyboardTable, 'keyboard'),
    ('mouse', MouseTable, 'mouse'),
    ('headphone', HeadphoneTable, 'headphone'),
    ('pentable', Pentable, 'pentable'),
    ('speaker', SpeakerTable, 'speaker'),
    ('webcam', WebcamTable, 'webcam'),
)


def _assigned_machines_for_inventory_item(obj):
    """
    Return machine rows for an inventory item as:
    [({'name': 'machine_name - user_name', 'url': machine_detail_url}, 1), ...]
    """
    machine_map = {}
    model_class = obj.__class__

    if model_class == OperatingSystemTable:
        rows = (
            MachineTable.objects.filter(
                operating_system=obj,
                is_delete=False,
            )
            .select_related('member')
            .distinct()
            .order_by('name', 'pk')
        )
        for machine in rows:
            machine_name = (getattr(machine, 'name', '') or '').strip() or f'Machine #{machine.pk}'
            user_name = '—'
            if machine.member:
                user_name = (machine.member.get_full_name() or '').strip() or machine.member.username
            machine_map[machine.pk] = f'{machine_name} - {user_name}'
    else:
        component_key = next((key for key, model, _ in _COMPONENT_OPTIONS_CONFIG if model == model_class), None)
        if not component_key:
            return []

        through_meta = next((x for x in _MACHINE_THROUGH_SAVE if x[0] == component_key), None)
        if not through_meta:
            return []

        _, through_model, fk_attr = through_meta
        filters = {
            fk_attr: obj,
            'machine__is_delete': False,
        }
        rows = through_model.objects.filter(**filters).select_related('machine__member')
        for row in rows:
            machine = row.machine
            machine_name = (getattr(machine, 'name', '') or '').strip() or f'Machine #{machine.pk}'
            user_name = '—'
            if machine.member:
                user_name = (machine.member.get_full_name() or '').strip() or machine.member.username
            machine_map[machine.pk] = f'{machine_name} - {user_name}'

    items = []
    for machine_id, machine_name in sorted(machine_map.items(), key=lambda p: p[1].lower()):
        items.append(({
            'name': machine_name,
            'url': reverse('hardwareapp:machine_detail', args=[machine_id]),
        }, 1))
    return items


class InventoryAssignedMachinesDetailMixin:
    def render_to_response(self, context, **response_kwargs):
        fields = context.get('fields')
        if isinstance(fields, list):
            assigned_machines = _assigned_machines_for_inventory_item(self.object)
            fields.append({
                'label': 'Assigned Machine Count',
                'value': len(assigned_machines),
            })
            fields.append({
                'label': 'Assigned Machines',
                'data': assigned_machines,
            })
        return super().render_to_response(context, **response_kwargs)


def _save_machine_through_components(form, machine):
    """Clear and recreate through rows from form parsed component entries (JSON)."""
    for field_name, through_model, fk_attr in _MACHINE_THROUGH_SAVE:
        through_model.objects.filter(machine=machine).delete()
        entries = form.cleaned_data.get(field_name + '_entries') or []
        model_class = next((m[1] for m in _COMPONENT_OPTIONS_CONFIG if m[0] == field_name), None)
        for entry in entries:
            comp_id = entry.get('id')
            qty = max(1, int(entry.get('qty', 1)))
            if not comp_id or not model_class:
                continue
            try:
                comp = model_class.objects.get(pk=comp_id)
                through_model.objects.create(machine=machine, **{fk_attr: comp, 'quantity': qty})
            except model_class.DoesNotExist:
                pass
    from hardwareapp.machine_history import log_components_snapshot

    log_components_snapshot(machine)


def _validate_machine_component_remaining(form, machine=None):
    """
    Validate requested machine component quantities against component.remaining.
    On update, quantities already assigned to this machine are allowed.
    """
    for field_name, through_model, fk_attr in _MACHINE_THROUGH_SAVE:
        entries = form.cleaned_data.get(field_name + '_entries') or []
        if not entries:
            continue

        model_class = next((m[1] for m in _COMPONENT_OPTIONS_CONFIG if m[0] == field_name), None)
        if not model_class:
            continue

        requested_by_id = {}
        for entry in entries:
            comp_id = entry.get('id')
            qty = max(1, int(entry.get('qty', 1)))
            requested_by_id[comp_id] = requested_by_id.get(comp_id, 0) + qty

        existing_on_machine = {}
        if machine and machine.pk:
            for row in through_model.objects.filter(machine=machine):
                comp = getattr(row, fk_attr, None)
                if not comp:
                    continue
                existing_on_machine[comp.pk] = existing_on_machine.get(comp.pk, 0) + getattr(row, 'quantity', 1)

        for comp_id, requested_qty in requested_by_id.items():
            try:
                comp = model_class.objects.get(pk=comp_id)
            except model_class.DoesNotExist:
                form.add_error(field_name + '_entries', 'Invalid component selected.')
                break

            remaining_qty = max(0, int(getattr(comp, 'remaining', 0) or 0))
            already_on_this_machine = existing_on_machine.get(comp.pk, 0)
            allowed_qty = remaining_qty + already_on_this_machine

            if requested_qty > allowed_qty:
                form.add_error(
                    field_name + '_entries',
                    (
                        f'Not enough stock for {getattr(comp, "name", "selected component")}. '
                        f'Remaining: {remaining_qty}, already on this machine: {already_on_this_machine}, '
                        f'requested: {requested_qty}.'
                    ),
                )
                break


class MachineComponentOptionsAPIView(AutoPermissionRequiredMixin, View):
    """API: GET returns component options for machine form (id, text). Not scoped by machine team."""

    def get(self, request):
        result = {'operating_system': []}
        for os in OperatingSystemTable.objects.filter(is_delete=False).order_by('name')[:200]:
            result['operating_system'].append({'id': os.pk, 'text': _component_option_label(os)})
        for key, model_class, _ in _COMPONENT_OPTIONS_CONFIG:
            qs = (
                model_class.objects.filter(is_delete=False)
                .filter(Q(remaining__gt=0) | Q(assign__gt=0))
                .distinct()
                .order_by('name')[:500]
            )
            result[key] = [
                {'id': obj.pk, 'text': _component_option_label(obj), 'remaining': getattr(obj, 'remaining', 0)}
                for obj in qs
            ]
        return JsonResponse(result)


# ---------- Machine (first in hardware) ----------
class MachineListView(AutoPermissionRequiredMixin, ListView):
    model = MachineTable
    template_name = 'hardwareapp/machine/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Machines'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Code', 'Member', 'Actions']
        context.update(machine_list_extras(self.request))
        return context


class MachineListDataView(AutoPermissionRequiredMixin, View):
    model = MachineTable

    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = MachineTable.objects.filter(is_delete=False).select_related('member', 'team')
        qs = apply_machine_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            sv = params['search_value']
            qs = qs.filter(
                Q(name__icontains=sv)
                | Q(code__icontains=sv)
                | Q(description__icontains=sv)
                | Q(member__username__icontains=sv)
                | Q(member__first_name__icontains=sv)
                | Q(member__last_name__icontains=sv)
                | Q(member__email__icontains=sv)
                | Q(team__name__icontains=sv)
            )
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'code', 'member__username']
        if 0 <= params['order_column'] < len(order_cols):
            order_field = order_cols[params['order_column']]
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_field}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('hardwareapp.view_machinetable')
        can_edit = request.user.has_perm('hardwareapp.change_machinetable')
        can_copy = request.user.has_perm('hardwareapp.add_machinetable')
        can_delete = request.user.has_perm('hardwareapp.delete_machinetable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {'url_name': 'hardwareapp:machine_detail', 'pk': obj.pk, 'label': obj.name or '—', 'can_view': can_view},
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'hardwareapp:machine_detail',
                    'update_url_name': 'hardwareapp:machine_update',
                    'copy_url_name': 'hardwareapp:machine_copy',
                    'delete_url_name': 'hardwareapp:machine_delete',
                    'history_url_name': 'hardwareapp:machine_history',
                    'obj': obj,
                    'can_view': can_view,
                    'can_view_history': can_view,
                    'can_edit': can_edit,
                    'can_copy': can_copy,
                    'can_delete': can_delete,
                },
                request=request,
            )
            member_label = '—'
            if obj.member_id and obj.member:
                member_label = (obj.member.username or '—')
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.code or '—', member_label, actions_cell])
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class MachineDetailView(AutoPermissionRequiredMixin, DetailView):
    model = MachineTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name or 'Machine'
        obj = self.object
        context['fields'] = [
            {"label": "Name", "value": obj.name},
            {"label": "Code", "value": obj.code},
            {"label": "Team", "value": obj.team.name if obj.team else "—"},
            {"label": "Department", "value": obj.department.name if obj.department else "—"},
            {
                "label": "Member",
                "value": (
                    (obj.member.get_full_name() or "").strip() or obj.member.username
                    if obj.member else "—"
                ),
            },
            {
                "label": "Operating System(s)",
                "value": ", ".join(
                    [
                        f"{os.name} ({os.version})" if os.version else os.name
                        for os in obj.operating_system.all()
                    ]
                ) or "—",
            },
            {"label": "Description", "value": obj.description or "—"},
        ]
        context['components'] = [
            {"label": "Processor(s)", "data": obj.get_processor_quantities()},
            {"label": "RAM", "data": obj.get_ram_quantities()},
            {"label": "SSD(s)", "data": obj.get_ssd_quantities()},
            {"label": "Motherboard(s)", "data": obj.get_motherboard_quantities()},
            {"label": "Power Supply", "data": obj.get_power_supply_quantities()},
            {"label": "Cabinet(s)", "data": obj.get_cabinet_quantities()},
            {"label": "Liquid Cooler(s)", "data": obj.get_liquid_cooler_quantities()},
            {"label": "Graphics Card(s)", "data": obj.get_graphics_card_quantities()},
            {"label": "HDD(s)", "data": obj.get_hdd_quantities()},
            {"label": "UPS", "data": obj.get_ups_quantities()},
            {"label": "Monitor(s)", "data": obj.get_monitor_quantities()},
            {"label": "Keyboard(s)", "data": obj.get_keyboard_quantities()},
            {"label": "Mouse", "data": obj.get_mouse_quantities()},
            {"label": "Headphone(s)", "data": obj.get_headphone_quantities()},
            {"label": "Pen Tablets(s)", "data": obj.get_pentable_quantities()},
            {"label": "Speaker(s)", "data": obj.get_speaker_quantities()},
            {"label": "Webcam(s)", "data": obj.get_webcam_quantities()},
        ]

        context['update_url'] = reverse('hardwareapp:machine_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:machine_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:machine_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:machine_list')

          #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_machinetable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_machinetable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_machinetable')
        context['history_url'] = reverse('hardwareapp:machine_history', args=[obj.pk])
        context['can_view_history'] = self.request.user.has_perm('hardwareapp.view_machinetable')

        return context


class MachineHistoryView(AutoPermissionRequiredMixin, DetailView):
    """Timeline of machine lifecycle, assignments, OS changes, and hardware configuration saves."""

    model = MachineTable
    template_name = 'hardwareapp/machine/history.html'
    context_object_name = 'machine'

    def get_queryset(self):
        return MachineTable.objects.filter(is_delete=False).select_related('team', 'department', 'member', 'createdby')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        machine = self.object
        context['title'] = f'History — {machine.name or machine.code or "Machine"}'
        entries = list(
            MachineHistoryEntry.objects.filter(machine=machine)
            .select_related('created_by')
            .order_by('-created_at')
        )
        context['entries'] = entries

        member_events = [e for e in entries if e.event_type == MachineHistoryEntry.EventType.MEMBER_CHANGED]
        context['member_change_count'] = len(member_events)
        assigned_ids = set()
        for e in member_events:
            tid = e.metadata.get('to_user_id')
            if tid:
                assigned_ids.add(tid)
        context['unique_assigned_user_ids'] = len(assigned_ids)
        context['list_url'] = reverse('hardwareapp:machine_list')
        context['detail_url'] = reverse('hardwareapp:machine_detail', args=[machine.pk])
        context['update_url'] = reverse('hardwareapp:machine_update', args=[machine.pk])
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_machinetable')
        return context


class MachineCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = MachineTable
    form_class = MachineForm
    template_name = 'hardwareapp/machine/form.html'
    success_url = reverse_lazy('hardwareapp:machine_list')
    success_message = 'Machine created Successfully.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Machine'
        context['machine_api_component_options_url'] = reverse_lazy('hardwareapp:machine_api_component_options')
        context['component_types'] = _machine_component_types()
        context['machine_component_totals_json'] = '{}'
        return context

    def form_valid(self, form):
        _validate_machine_component_remaining(form)
        if form.errors:
            return self.form_invalid(form)
        self.object = form.save()
        self.object.operating_system.set(form.cleaned_data.get('operating_system') or [])
        _save_machine_through_components(form, self.object)
        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


def _machine_component_types():
    """List of (key, label, required) for machine form component sections."""
    required = {'processor', 'ram', 'ssd', 'motherboard', 'power_supply', 'cabinet', 'liquid_cooler'}
    labels = {
        'processor': 'Processor', 'ram': 'RAM', 'ssd': 'SSD', 'motherboard': 'Motherboard',
        'power_supply': 'Power Supply', 'cabinet': 'Cabinet', 'liquid_cooler': 'Liquid Cooler',
        'graphics_card': 'Graphics Card', 'hdd': 'HDD', 'ups': 'UPS', 'monitor': 'Monitor',
        'keyboard': 'Keyboard', 'mouse': 'Mouse', 'headphone': 'Headphone',
        'pentable': 'Pen Tablets', 'speaker': 'Speaker', 'webcam': 'Webcam',
    }
    return [(key, labels.get(key, key), key in required) for key, _, _ in _COMPONENT_OPTIONS_CONFIG]


def _machine_initial_component_entries(machine):
    """Return dict of field_name_entries -> JSON list of {id, qty} for machine's through rows."""
    import json
    out = {}
    for field_name, through_model, fk_attr in _MACHINE_THROUGH_SAVE:
        entries = []
        for row in through_model.objects.filter(machine=machine).order_by('pk'):
            comp = getattr(row, fk_attr)
            if comp:
                entries.append({'id': comp.pk, 'qty': getattr(row, 'quantity', 1)})
        out[field_name + '_entries'] = json.dumps(entries)
    return out


def _machine_component_totals_on_machine(machine):
    """Return dict of type -> {component_id: total_qty} for fields already assigned to this machine."""
    import json
    out = {}
    for field_name, through_model, fk_attr in _MACHINE_THROUGH_SAVE:
        totals = {}
        for row in through_model.objects.filter(machine=machine):
            comp = getattr(row, fk_attr)
            if comp:
                qty = getattr(row, 'quantity', 1)
                totals[comp.pk] = totals.get(comp.pk, 0) + qty
        out[field_name] = totals
    return out


class MachineUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MachineTable
    form_class = MachineForm
    template_name = 'hardwareapp/machine/form.html'
    success_url = reverse_lazy('hardwareapp:machine_list')
    context_object_name = 'object'
    success_message = 'Machine updated.'

    def get_initial(self):
        initial = super().get_initial()
        if self.object:
            initial.update(_machine_initial_component_entries(self.object))
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Machine'
        context['machine_api_component_options_url'] = reverse_lazy('hardwareapp:machine_api_component_options')
        context['initial_component_entries'] = _machine_initial_component_entries(self.object) if self.object else {}
        context['component_types'] = _machine_component_types()
        # Per-component totals already assigned to this machine (for edit page: "X on this machine")
        if self.object:
            import json
            context['machine_component_totals_json'] = json.dumps(_machine_component_totals_on_machine(self.object))
        else:
            context['machine_component_totals_json'] = '{}'
        return context

    def form_valid(self, form):
        _validate_machine_component_remaining(form, machine=self.object)
        if form.errors:
            return self.form_invalid(form)
        self.object = form.save()
        self.object.operating_system.set(form.cleaned_data.get('operating_system') or [])
        _save_machine_through_components(form, self.object)
        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class MachineDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = MachineTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:machine_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Machine'
        #  what to show in UI
        context['object_display'] = (
            f"{obj.name} " if obj.code else obj.name
        )

        #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_machinetable'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:machine_list')

        return context


class MachineCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(MachineTable, pk=pk)
        copy = MachineTable(
            name=(f"{obj.name or ''} (Copy)".strip() or 'Machine (Copy)') if obj.name else 'Machine (Copy)',
            code=obj.code,
            description=obj.description,
            team=obj.team,
            department=obj.department,
            member=obj.member,
        )
        copy.save()
        copy.operating_system.set(obj.operating_system.filter(is_delete=False))
        for _through in (
            MachineProcessorThrough, MachineRAMThrough, MachineSSDThrough, MachineMotherboardThrough,
            MachinePowerSupplyThrough, MachineCabinetThrough, MachineLiquidCoolerThrough,
            MachineGraphicsCardThrough, MachineHDDThrough, MachineUPSThrough, MachineMonitorThrough,
            MachineKeyboardThrough, MachineMouseThrough, MachineHeadphoneThrough,
            MachinePentableThrough, MachineSpeakerThrough, MachineWebcamThrough,
        ):
            fk_attr = [f.name for f in _through._meta.get_fields() if f.many_to_one and f.name != 'machine'][0]
            for row in _through.objects.filter(machine=obj):
                comp = getattr(row, fk_attr)
                _through.objects.create(machine=copy, **{fk_attr: comp, 'quantity': row.quantity})
        from hardwareapp.machine_history import log_components_snapshot

        log_components_snapshot(copy)
        messages.success(request, 'Machine copied.')
        return redirect('hardwareapp:machine_list')


# ---------- Operating System ----------
class OSListView(AutoPermissionRequiredMixin, ListView):
    model = OperatingSystemTable
    template_name = 'hardwareapp/os/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Operating Systems'
        context['table_columns'] = ['Sl', 'Name', 'Version', 'Actions']
        context.update(os_list_extras(self.request))
        return context


class OSListDataView(AutoPermissionRequiredMixin, View):
    """JSON endpoint for DataTables server-side search, sort, pagination."""
    model = OperatingSystemTable

    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = OperatingSystemTable.objects.filter(is_delete=False)
        qs = apply_inventory_assignee_scope(qs, request)
        qs = apply_inventory_date_range(qs, request)
        records_total = qs.count()

        if params['search_value']:
            qs = qs.filter(
                Q(name__icontains=params['search_value'])
                | Q(version__icontains=params['search_value'])
            )
        records_filtered = qs.count()

        order_cols = ['id', 'name', 'version']
        if 0 <= params['order_column'] < len(order_cols):
            order_field = order_cols[params['order_column']]
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_field}')
        else:
            qs = qs.order_by('id')

        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('hardwareapp.view_operatingsystemtable')
        can_edit = request.user.has_perm('hardwareapp.change_operatingsystemtable')
        can_copy = request.user.has_perm('hardwareapp.add_operatingsystemtable')
        can_delete = request.user.has_perm('hardwareapp.delete_operatingsystemtable')

        data = []
        start = params['start']
        for idx, obj in enumerate(page):
            counter = start + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {
                    'url_name': 'hardwareapp:os_detail',
                    'pk': obj.pk,
                    'label': obj.name,
                    'can_view': can_view,
                },
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'hardwareapp:os_detail',
                    'update_url_name': 'hardwareapp:os_update',
                    'copy_url_name': 'hardwareapp:os_copy',
                    'delete_url_name': 'hardwareapp:os_delete',
                    'obj': obj,
                    'can_view': can_view,
                    'can_edit': can_edit,
                    'can_copy': can_copy,
                    'can_delete': can_delete,
                },
                request=request,
            )
            data.append([counter,name_cell, obj.version, actions_cell])

        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })

class OSDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = OperatingSystemTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        context['title'] = obj.name

        #  Fields for generic template
        context['fields'] = [
            {"label": "Name", "value": obj.name},
            {"label": "Version", "value": obj.version},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:os_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:os_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:os_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:os_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_operatingsystemtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_operatingsystemtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_operatingsystemtable')

        return context
   

class OSCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = OperatingSystemTable
    form_class = OperatingSystemForm
    template_name = 'hardwareapp/os/form.html'
    success_url = reverse_lazy('hardwareapp:os_list')
    success_message = 'Operating system created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add OS'
        return context


class OSUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = OperatingSystemTable
    form_class = OperatingSystemForm
    template_name = 'hardwareapp/os/form.html'
    success_url = reverse_lazy('hardwareapp:os_list')
    context_object_name = 'object'
    success_message = 'Operating system updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit OS'
        return context


class OSDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = OperatingSystemTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:os_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Operating System'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_os'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:os_list')
        return context

   


class OSCopyView(AutoPermissionRequiredMixin, View):
    model = OperatingSystemTable

    def get(self, request, pk):
        obj = get_object_or_404(OperatingSystemTable, pk=pk)
        copy = OperatingSystemTable(name=f"{obj.name} (Copy)", version=obj.version)
        copy.save()
        messages.success(request, 'Operating system copied.')
        return redirect('hardwareapp:os_list')


# ---------- Processor ----------
class ProcessorListView(AutoPermissionRequiredMixin, ListView):
    model = ProcessorTable
    template_name = 'hardwareapp/processor/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Processors'
        # Column labels for the processor list table (used by the template)
        context['table_columns'] = [
            'Sl',
            'Team',
            'Name',
            'Brand',
            'Model',
            'memory',
            'Cores',
            'Threads',
            'Frequency',
            'Cache',
            'Quantity',
            'Assign',
            'Remaining',
            'Issue',
            'Actions',
        ]
        context.update(inventory_list_extras(self.request, ProcessorTable))
        return context


class ProcessorListDataView(AutoPermissionRequiredMixin, View):
    """JSON endpoint for DataTables server-side search, sort, pagination."""
    model = ProcessorTable

    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = ProcessorTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()

        if params['search_value']:
            sv = params['search_value']
            qs = qs.filter(
                Q(name__icontains=sv)
                | Q(brand__icontains=sv)
                | Q(model__icontains=sv)
                | Q(architecture__icontains=sv)
                | Q(frequency__icontains=sv)
                | Q(cache__icontains=sv)
                | Q(team__name__icontains=sv)
            )
        records_filtered = qs.count()

        order_cols = [
            'id',
            'team__name',
            'name',
            'brand',
            'model',
            'architecture',
            'cores',
            'threads',
            'frequency',
            'cache',
            'quantity',
            'assign',
            'remaining',
        ]
        if 0 <= params['order_column'] < len(order_cols):
            order_field = order_cols[params['order_column']]
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_field}')
        else:
            qs = qs.order_by('id')

        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('hardwareapp.view_processortable')
        can_edit = request.user.has_perm('hardwareapp.change_processortable')
        can_copy = request.user.has_perm('hardwareapp.add_processortable')
        can_delete = request.user.has_perm('hardwareapp.delete_processortable')

        issue_totals = _issue_totals_for_component('processor', page)
        data = []
        start = params['start']
        for idx, obj in enumerate(page):
            counter = start + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {
                    'url_name': 'hardwareapp:processor_detail',
                    'pk': obj.pk,
                    'label': obj.name,
                    'can_view': can_view,
                },
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'hardwareapp:processor_detail',
                    'update_url_name': 'hardwareapp:processor_update',
                    'copy_url_name': 'hardwareapp:processor_copy',
                    'delete_url_name': 'hardwareapp:processor_delete',
                    'obj': obj,
                    'can_view': can_view,
                    'can_edit': can_edit,
                    'can_copy': can_copy,
                    'can_delete': can_delete,
                },
                request=request,
            )
            data.append([
                counter,
                _inventory_table_team_name(obj),
                name_cell,
                obj.brand,
                obj.model,
                obj.architecture,
                obj.cores,
                obj.threads,
                obj.frequency,
                obj.cache,
                obj.quantity,
                obj.assign,
                obj.remaining,
                issue_totals.get(obj.pk, 0),
                actions_cell,
            ])

        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class ProcessorDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = ProcessorTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Architecture", "value": obj.architecture},
             {"label": "cores", "value": obj.cores},
            {"label": "Threads", "value": obj.threads},
            {"label": "Frequency", "value": obj.frequency},
            {"label": "Cache", "value": obj.cache},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:processor_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:processor_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:processor_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:processor_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_processortable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_processortable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_processortable')

        return context


class ProcessorCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProcessorTable
    form_class = ProcessorForm
    template_name = 'hardwareapp/processor/form.html'
    success_url = reverse_lazy('hardwareapp:processor_list')
    success_message = 'Processor created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Processor'
        return context


class ProcessorUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProcessorTable
    form_class = ProcessorForm
    template_name = 'hardwareapp/processor/form.html'
    success_url = reverse_lazy('hardwareapp:processor_list')
    context_object_name = 'object'
    success_message = 'Processor updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Processor'
        return context


class ProcessorDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = ProcessorTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:processor_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Processor'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_processor'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:processor_list')
        return context


class ProcessorCopyView(AutoPermissionRequiredMixin, View):
    model = ProcessorTable

    def get(self, request, pk):
        obj = get_object_or_404(ProcessorTable, pk=pk)
        copy = ProcessorTable(
            team=obj.team,
            name=f"{obj.name or ''} (Copy)".strip() or 'Processor (Copy)',
            brand=obj.brand,
            model=obj.model,
            architecture=obj.architecture,
            cores=obj.cores,
            threads=obj.threads,
            frequency=obj.frequency,
            cache=obj.cache,
            quantity=obj.quantity,
            assign=obj.assign,
            remaining=obj.remaining,
        )
        copy.save()
        messages.success(request, 'Processor copied.')
        return redirect('hardwareapp:processor_list')


# ---------- Graphics Card ----------
class GraphicsCardListView(AutoPermissionRequiredMixin, ListView):
    model = GraphicsCardTable
    template_name = 'hardwareapp/graphics_card/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Graphics Cards'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Memory (GB)', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, GraphicsCardTable))
        return context


class GraphicsCardListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = GraphicsCardTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(
                Q(name__icontains=params['search_value'])
                | Q(brand__icontains=params['search_value'])
                | Q(model__icontains=params['search_value'])
                | Q(team__name__icontains=params['search_value'])
            )
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'memory', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_field = order_cols[params['order_column']]
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_field}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('graphics_card', page)
        can_view = request.user.has_perm('hardwareapp.view_graphicscardtable')
        can_edit = request.user.has_perm('hardwareapp.change_graphicscardtable')
        can_copy = request.user.has_perm('hardwareapp.add_graphicscardtable')
        can_delete = request.user.has_perm('hardwareapp.delete_graphicscardtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {
                'url_name': 'hardwareapp:graphics_card_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view,
            }, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {
                'detail_url_name': 'hardwareapp:graphics_card_detail', 'update_url_name': 'hardwareapp:graphics_card_update',
                'copy_url_name': 'hardwareapp:graphics_card_copy', 'delete_url_name': 'hardwareapp:graphics_card_delete',
                'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete,
            }, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.memory, obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class GraphicsCardDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
       model = GraphicsCardTable
       template_name = 'hardwareapp/common-html/details.html'
       context_object_name = 'object'

       def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            obj = self.object
            context['title'] = obj.name
            #  Fields for generic template
            context['fields'] = [
                {"label": "Team", "value": obj.team.name},
                {"label": "Name", "value": obj.name},
                {"label": "Brand", "value": obj.brand},
                {"label": "Model", "value": obj.model},
                {"label": "Memory (GB)", "value": obj.memory},
                {"label": "Quantity", "value": obj.quantity},
            ]

        #  Buttons (same pattern you used before)
            context['update_url'] = reverse('hardwareapp:graphics_card_update', args=[obj.pk])
            context['copy_url'] = reverse('hardwareapp:graphics_card_copy', args=[obj.pk])
            context['delete_url'] = reverse('hardwareapp:graphics_card_delete', args=[obj.pk])
            context['list_url'] = reverse('hardwareapp:graphics_card_list')

            #  Permissions
            context['can_edit'] = self.request.user.has_perm('hardwareapp.change_graphicscardtable')
            context['can_copy'] = self.request.user.has_perm('hardwareapp.add_graphicscardtable')
            context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_graphicscardtable')

            return context


class GraphicsCardCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = GraphicsCardTable
    form_class = GraphicsCardForm
    template_name = 'hardwareapp/graphics_card/form.html'
    success_url = reverse_lazy('hardwareapp:graphics_card_list')
    success_message = 'Graphics card created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Graphics Card'
        return context


class GraphicsCardUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = GraphicsCardTable
    form_class = GraphicsCardForm
    template_name = 'hardwareapp/graphics_card/form.html'
    success_url = reverse_lazy('hardwareapp:graphics_card_list')
    context_object_name = 'object'
    success_message = 'Graphics card updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Graphics Card'
        return context


class GraphicsCardDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = GraphicsCardTable
    template_name = 'hardwareapp/common-html/delete.html'

    success_url = reverse_lazy('hardwareapp:graphics_card_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Graphics Card'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_graphics_card'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:graphics_card_list')
        return context


class GraphicsCardCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(GraphicsCardTable, pk=pk)
        copy = GraphicsCardTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Graphics Card (Copy)', brand=obj.brand, model=obj.model, memory=obj.memory, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Graphics card copied.')
        return redirect('hardwareapp:graphics_card_list')


# ---------- Motherboard ----------
class MotherboardListView(AutoPermissionRequiredMixin, ListView):
    model = MotherboardTable
    template_name = 'hardwareapp/motherboard/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Motherboards'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Socket', 'Memory Slots', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, MotherboardTable))
        return context


class MotherboardListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = MotherboardTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(socket__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'socket', 'memory_slots', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('motherboard', page)
        can_view = request.user.has_perm('hardwareapp.view_motherboardtable')
        can_edit = request.user.has_perm('hardwareapp.change_motherboardtable')
        can_copy = request.user.has_perm('hardwareapp.add_motherboardtable')
        can_delete = request.user.has_perm('hardwareapp.delete_motherboardtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:motherboard_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:motherboard_detail', 'update_url_name': 'hardwareapp:motherboard_update', 'copy_url_name': 'hardwareapp:motherboard_copy', 'delete_url_name': 'hardwareapp:motherboard_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.socket or '', obj.memory_slots, obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class MotherboardDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = MotherboardTable   
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Socket", "value": obj.socket},
             {"label": "Memory Slots", "value": obj.memory_slots},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:motherboard_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:motherboard_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:motherboard_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:motherboard_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_motherboardtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_motherboardtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_motherboardtable')

        return context


class MotherboardCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = MotherboardTable
    form_class = MotherboardForm
    template_name = 'hardwareapp/motherboard/form.html'
    success_url = reverse_lazy('hardwareapp:motherboard_list')
    success_message = 'Motherboard created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Motherboard'
        return context


class MotherboardUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MotherboardTable
    form_class = MotherboardForm
    template_name = 'hardwareapp/motherboard/form.html'
    success_url = reverse_lazy('hardwareapp:motherboard_list')
    context_object_name = 'object'
    success_message = 'Motherboard updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Motherboard'
        return context


class MotherboardDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = MotherboardTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:motherboard_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Motherboard'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_motherboard_list'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:motherboard_list')
        return context


class MotherboardCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(MotherboardTable, pk=pk)
        copy = MotherboardTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Motherboard (Copy)', brand=obj.brand, model=obj.model, socket=obj.socket, memory_slots=obj.memory_slots, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Motherboard copied.')
        return redirect('hardwareapp:motherboard_list')


# ---------- RAM ----------
class RAMListView(AutoPermissionRequiredMixin, ListView):
    model = RAMTable
    template_name = 'hardwareapp/ram/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'RAM'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Memory (GB)', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, RAMTable))
        return context


class RAMListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = RAMTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'memory', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('ram', page)
        can_view = request.user.has_perm('hardwareapp.view_ramtable')
        can_edit = request.user.has_perm('hardwareapp.change_ramtable')
        can_copy = request.user.has_perm('hardwareapp.add_ramtable')
        can_delete = request.user.has_perm('hardwareapp.delete_ramtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:ram_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:ram_detail', 'update_url_name': 'hardwareapp:ram_update', 'copy_url_name': 'hardwareapp:ram_copy', 'delete_url_name': 'hardwareapp:ram_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.memory, obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class RAMDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = RAMTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Memory (GB)", "value": obj.memory},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:ram_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:ram_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:ram_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:ram_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_ramtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_ramtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_ramtable')

        return context


class RAMCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = RAMTable
    form_class = RAMForm
    template_name = 'hardwareapp/ram/form.html'
    success_url = reverse_lazy('hardwareapp:ram_list')
    success_message = 'RAM created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add RAM'
        return context


class RAMUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = RAMTable
    form_class = RAMForm
    template_name = 'hardwareapp/ram/form.html'
    success_url = reverse_lazy('hardwareapp:ram_list')
    context_object_name = 'object'
    success_message = 'RAM updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit RAM'
        return context


class RAMDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = RAMTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:ram_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete RAM'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_ram_list'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:ram_list')
        return context

class RAMCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(RAMTable, pk=pk)
        copy = RAMTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'RAM (Copy)', brand=obj.brand, model=obj.model, memory=obj.memory, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'RAM copied.')
        return redirect('hardwareapp:ram_list')


# ---------- HDD ----------
class HDListView(AutoPermissionRequiredMixin, ListView):
    model = HDDTable
    template_name = 'hardwareapp/hdd/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'HDD'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Capacity (GB)', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, HDDTable))
        return context


class HDListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = HDDTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'capacity', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('hdd', page)
        can_view = request.user.has_perm('hardwareapp.view_hddtable')
        can_edit = request.user.has_perm('hardwareapp.change_hddtable')
        can_copy = request.user.has_perm('hardwareapp.add_hddtable')
        can_delete = request.user.has_perm('hardwareapp.delete_hddtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:hdd_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:hdd_detail', 'update_url_name': 'hardwareapp:hdd_update', 'copy_url_name': 'hardwareapp:hdd_copy', 'delete_url_name': 'hardwareapp:hdd_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.capacity, obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class HDDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = HDDTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
            {"label": "Capacity", "value": obj.capacity},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:hdd_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:hdd_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:hdd_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:hdd_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_hddtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_hddtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_hddtable')

        return context


class HDCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = HDDTable
    form_class = HDForm
    template_name = 'hardwareapp/hdd/form.html'
    success_url = reverse_lazy('hardwareapp:hdd_list')
    success_message = 'HDD created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add HDD'
        return context


class HDUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HDDTable
    form_class = HDForm
    template_name = 'hardwareapp/hdd/form.html'
    success_url = reverse_lazy('hardwareapp:hdd_list')
    context_object_name = 'object'
    success_message = 'HDD updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit HDD'
        return context


class HDDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = HDDTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:hdd_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete HDD'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_hdd'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:hdd_list')
        return context


class HDCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(HDDTable, pk=pk)
        copy = HDDTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'HDD (Copy)', brand=obj.brand, model=obj.model, capacity=obj.capacity, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'HDD copied.')
        return redirect('hardwareapp:hdd_list')


# ---------- SSD ----------
class SSDListView(AutoPermissionRequiredMixin, ListView):
    model = SSDTable
    template_name = 'hardwareapp/ssd/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'SSD'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Capacity (GB)', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, SSDTable))
        return context


class SSDListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = SSDTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'capacity', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('ssd', page)
        can_view = request.user.has_perm('hardwareapp.view_ssdtable')
        can_edit = request.user.has_perm('hardwareapp.change_ssdtable')
        can_copy = request.user.has_perm('hardwareapp.add_ssdtable')
        can_delete = request.user.has_perm('hardwareapp.delete_ssdtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:ssd_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:ssd_detail', 'update_url_name': 'hardwareapp:ssd_update', 'copy_url_name': 'hardwareapp:ssd_copy', 'delete_url_name': 'hardwareapp:ssd_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.capacity, obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class SSDDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = SSDTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Capacity", "value": obj.capacity},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:ssd_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:ssd_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:ssd_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:ssd_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_ssdtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_ssdtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_ssdtable')

        return context


class SSDCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = SSDTable
    form_class = SSDForm
    template_name = 'hardwareapp/ssd/form.html'
    success_url = reverse_lazy('hardwareapp:ssd_list')
    success_message = 'SSD created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add SSD'
        return context


class SSDUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SSDTable
    form_class = SSDForm
    template_name = 'hardwareapp/ssd/form.html'
    success_url = reverse_lazy('hardwareapp:ssd_list')
    context_object_name = 'object'
    success_message = 'SSD updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit SSD'
        return context


class SSDDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = SSDTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:ssd_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete SDD'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_ssd'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:ssd_list')
        return context


class SSDCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(SSDTable, pk=pk)
        copy = SSDTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'SSD (Copy)', brand=obj.brand, model=obj.model, capacity=obj.capacity, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'SSD copied.')
        return redirect('hardwareapp:ssd_list')


# ---------- Liquid Cooler ----------
class LiquidCoolerListView(AutoPermissionRequiredMixin, ListView):
    model = LiquidCoolerTable
    template_name = 'hardwareapp/liquid_cooler/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Liquid Coolers'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Is Liquid', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, LiquidCoolerTable))
        return context


class LiquidCoolerListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = LiquidCoolerTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining', 'is_liquid']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('liquid_cooler', page)
        can_view = request.user.has_perm('hardwareapp.view_liquidcoolertable')
        can_edit = request.user.has_perm('hardwareapp.change_liquidcoolertable')
        can_copy = request.user.has_perm('hardwareapp.add_liquidcoolertable')
        can_delete = request.user.has_perm('hardwareapp.delete_liquidcoolertable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:liquid_cooler_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:liquid_cooler_detail', 'update_url_name': 'hardwareapp:liquid_cooler_update', 'copy_url_name': 'hardwareapp:liquid_cooler_copy', 'delete_url_name': 'hardwareapp:liquid_cooler_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, 'Yes' if obj.is_liquid else 'No', issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class LiquidCoolerDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = LiquidCoolerTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
            #  {"label": "Cache", "value": obj.cache},
             {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:liquid_cooler_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:liquid_cooler_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:liquid_cooler_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:liquid_cooler_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_liquidcoolertable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_liquidcoolertable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_liquidcoolertable')

        return context


class LiquidCoolerCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = LiquidCoolerTable
    form_class = LiquidCoolerForm
    template_name = 'hardwareapp/liquid_cooler/form.html'
    success_url = reverse_lazy('hardwareapp:liquid_cooler_list')
    success_message = 'Liquid cooler created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Liquid Cooler'
        return context


class LiquidCoolerUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = LiquidCoolerTable
    form_class = LiquidCoolerForm
    template_name = 'hardwareapp/liquid_cooler/form.html'
    success_url = reverse_lazy('hardwareapp:liquid_cooler_list')
    context_object_name = 'object'
    success_message = 'Liquid cooler updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Liquid Cooler'
        return context


class LiquidCoolerDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = LiquidCoolerTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:liquid_cooler_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Liquid Cooler'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_liquid_cooler'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:liquid_cooler_list')
        return context


class LiquidCoolerCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(LiquidCoolerTable, pk=pk)
        copy = LiquidCoolerTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Liquid Cooler (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining, is_liquid=obj.is_liquid)
        copy.save()
        messages.success(request, 'Liquid cooler copied.')
        return redirect('hardwareapp:liquid_cooler_list')


# ---------- UPS ----------
class UPSListView(AutoPermissionRequiredMixin, ListView):
    model = UPSTable
    template_name = 'hardwareapp/ups/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'UPS'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, UPSTable))
        return context


class UPSListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = UPSTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('ups', page)
        can_view = request.user.has_perm('hardwareapp.view_upstable')
        can_edit = request.user.has_perm('hardwareapp.change_upstable')
        can_copy = request.user.has_perm('hardwareapp.add_upstable')
        can_delete = request.user.has_perm('hardwareapp.delete_upstable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:ups_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:ups_detail', 'update_url_name': 'hardwareapp:ups_update', 'copy_url_name': 'hardwareapp:ups_copy', 'delete_url_name': 'hardwareapp:ups_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class UPSDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = UPSTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model}, 
             {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:ups_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:ups_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:ups_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:ups_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_upstable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_upstable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_upstable')

        return context


class UPSCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = UPSTable
    form_class = UPSForm
    template_name = 'hardwareapp/ups/form.html'
    success_url = reverse_lazy('hardwareapp:ups_list')
    success_message = 'UPS created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add UPS'
        return context


class UPSUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = UPSTable
    form_class = UPSForm
    template_name = 'hardwareapp/ups/form.html'
    success_url = reverse_lazy('hardwareapp:ups_list')
    context_object_name = 'object'
    success_message = 'UPS updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit UPS'
        return context


class UPSDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = UPSTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:ups_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete UPS'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_ups'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:ups_list')
        return context


class UPSCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(UPSTable, pk=pk)
        copy = UPSTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'UPS (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'UPS copied.')
        return redirect('hardwareapp:ups_list')


# ---------- Monitor ----------
class MonitorListView(AutoPermissionRequiredMixin, ListView):
    model = MonitorTable
    template_name = 'hardwareapp/monitor/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Monitors'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, MonitorTable))
        return context


class MonitorListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = MonitorTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('monitor', page)
        can_view = request.user.has_perm('hardwareapp.view_monitortable')
        can_edit = request.user.has_perm('hardwareapp.change_monitortable')
        can_copy = request.user.has_perm('hardwareapp.add_monitortable')
        can_delete = request.user.has_perm('hardwareapp.delete_monitortable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:monitor_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:monitor_detail', 'update_url_name': 'hardwareapp:monitor_update', 'copy_url_name': 'hardwareapp:monitor_copy', 'delete_url_name': 'hardwareapp:monitor_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class MonitorDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = MonitorTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
            
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:monitor_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:monitor_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:monitor_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:monitor_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_monitortable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_monitortable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_monitortable')

        return context


class MonitorCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = MonitorTable
    form_class = MonitorForm
    template_name = 'hardwareapp/monitor/form.html'
    success_url = reverse_lazy('hardwareapp:monitor_list')
    success_message = 'Monitor created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Monitor'
        return context


class MonitorUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MonitorTable
    form_class = MonitorForm
    template_name = 'hardwareapp/monitor/form.html'
    success_url = reverse_lazy('hardwareapp:monitor_list')
    context_object_name = 'object'
    success_message = 'Monitor updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Monitor'
        return context


class MonitorDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = MonitorTable
    template_name = 'hardwareapp/common-html/delete.html'

    success_url = reverse_lazy('hardwareapp:monitor_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Monitorm'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_monitor'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:monitor_list')
        return context


class MonitorCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(MonitorTable, pk=pk)
        copy = MonitorTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Monitor (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Monitor copied.')
        return redirect('hardwareapp:monitor_list')


# ---------- Keyboard ----------
class KeyboardListView(AutoPermissionRequiredMixin, ListView):
    model = KeyboardTable
    template_name = 'hardwareapp/keyboard/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Keyboards'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, KeyboardTable))
        return context


class KeyboardListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = KeyboardTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('keyboard', page)
        can_view = request.user.has_perm('hardwareapp.view_keyboardtable')
        can_edit = request.user.has_perm('hardwareapp.change_keyboardtable')
        can_copy = request.user.has_perm('hardwareapp.add_keyboardtable')
        can_delete = request.user.has_perm('hardwareapp.delete_keyboardtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:keyboard_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:keyboard_detail', 'update_url_name': 'hardwareapp:keyboard_update', 'copy_url_name': 'hardwareapp:keyboard_copy', 'delete_url_name': 'hardwareapp:keyboard_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class KeyboardDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = KeyboardTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:keyboard_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:keyboard_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:keyboard_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:keyboard_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_keyboardtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_keyboardtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_keyboardtable')

        return context


class KeyboardCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = KeyboardTable
    form_class = KeyboardForm
    template_name = 'hardwareapp/keyboard/form.html'
    success_url = reverse_lazy('hardwareapp:keyboard_list')
    success_message = 'Keyboard created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Keyboard'
        return context


class KeyboardUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = KeyboardTable
    form_class = KeyboardForm
    template_name = 'hardwareapp/keyboard/form.html'
    success_url = reverse_lazy('hardwareapp:keyboard_list')
    context_object_name = 'object'
    success_message = 'Keyboard updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Keyboard'
        return context


class KeyboardDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = KeyboardTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:keyboard_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Keyboard'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_keyboard'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:keyboard_list')
        return context


class KeyboardCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(KeyboardTable, pk=pk)
        copy = KeyboardTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Keyboard (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Keyboard copied.')
        return redirect('hardwareapp:keyboard_list')


# ---------- Mouse ----------
class MouseListView(AutoPermissionRequiredMixin, ListView):
    model = MouseTable
    template_name = 'hardwareapp/mouse/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mouse'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, MouseTable))
        return context


class MouseListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = MouseTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('mouse', page)
        can_view = request.user.has_perm('hardwareapp.view_mousetable')
        can_edit = request.user.has_perm('hardwareapp.change_mousetable')
        can_copy = request.user.has_perm('hardwareapp.add_mousetable')
        can_delete = request.user.has_perm('hardwareapp.delete_mousetable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:mouse_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:mouse_detail', 'update_url_name': 'hardwareapp:mouse_update', 'copy_url_name': 'hardwareapp:mouse_copy', 'delete_url_name': 'hardwareapp:mouse_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class MouseDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = MouseTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:mouse_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:mouse_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:mouse_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:mouse_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_mousetable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_mousetable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_mousetable')

        return context


class MouseCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = MouseTable
    form_class = MouseForm
    template_name = 'hardwareapp/mouse/form.html'
    success_url = reverse_lazy('hardwareapp:mouse_list')
    success_message = 'Mouse created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Mouse'
        return context


class MouseUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MouseTable
    form_class = MouseForm
    template_name = 'hardwareapp/mouse/form.html'
    success_url = reverse_lazy('hardwareapp:mouse_list')
    context_object_name = 'object'
    success_message = 'Mouse updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Mouse'
        return context


class MouseDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = MouseTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:mouse_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Mouse'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_mouse'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:mouse_list')
        return context


class MouseCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(MouseTable, pk=pk)
        copy = MouseTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Mouse (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Mouse copied.')
        return redirect('hardwareapp:mouse_list')


# ---------- Headphone ----------
class HeadphoneListView(AutoPermissionRequiredMixin, ListView):
    model = HeadphoneTable
    template_name = 'hardwareapp/headphone/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Headphones'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, HeadphoneTable))
        return context

class HeadphoneListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = HeadphoneTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('headphone', page)
        can_view = request.user.has_perm('hardwareapp.view_headphonetable')
        can_edit = request.user.has_perm('hardwareapp.change_headphonetable')
        can_copy = request.user.has_perm('hardwareapp.add_headphonetable')
        can_delete = request.user.has_perm('hardwareapp.delete_headphonetable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:headphone_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:headphone_detail', 'update_url_name': 'hardwareapp:headphone_update', 'copy_url_name': 'hardwareapp:headphone_copy', 'delete_url_name': 'hardwareapp:headphone_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class HeadphoneDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = HeadphoneTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:headphone_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:headphone_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:headphone_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:headphone_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_headphonetable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_headphonetable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_headphonetable')

        return context



class HeadphoneCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = HeadphoneTable
    form_class = HeadphoneForm
    template_name = 'hardwareapp/headphone/form.html'
    success_url = reverse_lazy('hardwareapp:headphone_list')
    success_message = 'Headphone created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Headphone'
        return context


class HeadphoneUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HeadphoneTable
    form_class = HeadphoneForm
    template_name = 'hardwareapp/headphone/form.html'
    success_url = reverse_lazy('hardwareapp:headphone_list')
    context_object_name = 'object'
    success_message = 'Headphone updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Headphone'
        return context


class HeadphoneDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = HeadphoneTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:headphone_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Headphone'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_headphone'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:headphone_list')
        return context


class HeadphoneCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(HeadphoneTable, pk=pk)
        copy = HeadphoneTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Headphone (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Headphone copied.')
        return redirect('hardwareapp:headphone_list')


# ---------- Pentable ----------
class PentableListView(AutoPermissionRequiredMixin, ListView):
    model = Pentable
    template_name = 'hardwareapp/pentable/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pen Tablets'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, Pentable))
        return context


class PentableListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = Pentable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('pentable', page)
        can_view = request.user.has_perm('hardwareapp.view_pentable')
        can_edit = request.user.has_perm('hardwareapp.change_pentable')
        can_copy = request.user.has_perm('hardwareapp.add_pentable')
        can_delete = request.user.has_perm('hardwareapp.delete_pentable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:pentable_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:pentable_detail', 'update_url_name': 'hardwareapp:pentable_update', 'copy_url_name': 'hardwareapp:pentable_copy', 'delete_url_name': 'hardwareapp:pentable_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class PentableDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = Pentable
    
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
           
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:pentable_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:pentable_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:pentable_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:pentable_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_pentable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_pentable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_pentable')

        return context


class PentableCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Pentable
    form_class = PentableForm
    template_name = 'hardwareapp/pentable/form.html'
    success_url = reverse_lazy('hardwareapp:pentable_list')
    success_message = 'Pen tablet created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Pen Tablet'
        return context


class PentableUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Pentable
    form_class = PentableForm
    template_name = 'hardwareapp/pentable/form.html'
    success_url = reverse_lazy('hardwareapp:pentable_list')
    context_object_name = 'object'
    success_message = 'Pen tablet updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Pen Tablet'
        return context


class PentableDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = Pentable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:pentable_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Pentable'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_pentable'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:pentable_list')
        return context


class PentableCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(Pentable, pk=pk)
        copy = Pentable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Pen Tablet (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Pen tablet copied.')
        return redirect('hardwareapp:pentable_list')


# ---------- Speaker ----------
class SpeakerListView(AutoPermissionRequiredMixin, ListView):
    model = SpeakerTable
    template_name = 'hardwareapp/speaker/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Speakers'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, SpeakerTable))
        return context


class SpeakerListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = SpeakerTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('speaker', page)
        can_view = request.user.has_perm('hardwareapp.view_speakertable')
        can_edit = request.user.has_perm('hardwareapp.change_speakertable')
        can_copy = request.user.has_perm('hardwareapp.add_speakertable')
        can_delete = request.user.has_perm('hardwareapp.delete_speakertable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:speaker_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:speaker_detail', 'update_url_name': 'hardwareapp:speaker_update', 'copy_url_name': 'hardwareapp:speaker_copy', 'delete_url_name': 'hardwareapp:speaker_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class SpeakerDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = SpeakerTable

    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
             
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:speaker_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:speaker_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:speaker_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:speaker_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_speakertable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_speakertable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_speakertable')

        return context


class SpeakerCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = SpeakerTable
    form_class = SpeakerForm
    template_name = 'hardwareapp/speaker/form.html'
    success_url = reverse_lazy('hardwareapp:speaker_list')
    success_message = 'Speaker created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Speaker'
        return context


class SpeakerUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SpeakerTable
    form_class = SpeakerForm
    template_name = 'hardwareapp/speaker/form.html'
    success_url = reverse_lazy('hardwareapp:speaker_list')
    context_object_name = 'object'
    success_message = 'Speaker updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Speaker'
        return context


class SpeakerDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = SpeakerTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:speaker_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Speaker'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_speaker'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:speaker_list')
        return context


class SpeakerCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(SpeakerTable, pk=pk)
        copy = SpeakerTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Speaker (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Speaker copied.')
        return redirect('hardwareapp:speaker_list')


# ---------- Webcam ----------
class WebcamListView(AutoPermissionRequiredMixin, ListView):
    model = WebcamTable
    template_name = 'hardwareapp/webcam/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Webcams'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, WebcamTable))
        return context


class WebcamListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = WebcamTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('webcam', page)
        can_view = request.user.has_perm('hardwareapp.view_webcamtable')
        can_edit = request.user.has_perm('hardwareapp.change_webcamtable')
        can_copy = request.user.has_perm('hardwareapp.add_webcamtable')
        can_delete = request.user.has_perm('hardwareapp.delete_webcamtable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:webcam_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:webcam_detail', 'update_url_name': 'hardwareapp:webcam_update', 'copy_url_name': 'hardwareapp:webcam_copy', 'delete_url_name': 'hardwareapp:webcam_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class WebcamDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = WebcamTable

    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
           
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:webcam_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:webcam_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:webcam_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:webcam_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_webcamtable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_webcamtable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_webcamtable')

        return context


class WebcamCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = WebcamTable
    form_class = WebcamForm
    template_name = 'hardwareapp/webcam/form.html'
    success_url = reverse_lazy('hardwareapp:webcam_list')
    success_message = 'Webcam created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Webcam'
        return context


class WebcamUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = WebcamTable
    form_class = WebcamForm
    template_name = 'hardwareapp/webcam/form.html'
    success_url = reverse_lazy('hardwareapp:webcam_list')
    context_object_name = 'object'
    success_message = 'Webcam updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Webcam'
        return context


class WebcamDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = WebcamTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:webcam_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete webcam'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_webcam'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:webcam_list')
        return context


class WebcamCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(WebcamTable, pk=pk)
        copy = WebcamTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Webcam (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Webcam copied.')
        return redirect('hardwareapp:webcam_list')


# ---------- Power Supply ----------
class PowerSupplyListView(AutoPermissionRequiredMixin, ListView):
    model = PowerSupplyTable
    template_name = 'hardwareapp/power_supply/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Power Supplies'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, PowerSupplyTable))
        return context


class PowerSupplyListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = PowerSupplyTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('power_supply', page)
        can_view = request.user.has_perm('hardwareapp.view_powersupplytable')
        can_edit = request.user.has_perm('hardwareapp.change_powersupplytable')
        can_copy = request.user.has_perm('hardwareapp.add_powersupplytable')
        can_delete = request.user.has_perm('hardwareapp.delete_powersupplytable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:power_supply_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:power_supply_detail', 'update_url_name': 'hardwareapp:power_supply_update', 'copy_url_name': 'hardwareapp:power_supply_copy', 'delete_url_name': 'hardwareapp:power_supply_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class PowerSupplyDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = PowerSupplyTable
    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
        
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:power_supply_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:power_supply_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:power_supply_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:power_supply_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_powersupplytable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_powersupplytable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_powersupplytable')

        return context


class PowerSupplyCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = PowerSupplyTable
    form_class = PowerSupplyForm
    template_name = 'hardwareapp/power_supply/form.html'
    success_url = reverse_lazy('hardwareapp:power_supply_list')
    success_message = 'Power supply created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Power Supply'
        return context


class PowerSupplyUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PowerSupplyTable
    form_class = PowerSupplyForm
    template_name = 'hardwareapp/power_supply/form.html'
    success_url = reverse_lazy('hardwareapp:power_supply_list')
    context_object_name = 'object'
    success_message = 'Power supply updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Power Supply'
        return context


class PowerSupplyDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = PowerSupplyTable
    template_name = 'hardwareapp/common-html/delete.html'
    success_url = reverse_lazy('hardwareapp:power_supply_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Power Supply'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_power_supply'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:power_supply_list')
        return context


class PowerSupplyCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(PowerSupplyTable, pk=pk)
        copy = PowerSupplyTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Power Supply (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Power supply copied.')
        return redirect('hardwareapp:power_supply_list')


# ---------- Cabinet ----------
class CabinetListView(AutoPermissionRequiredMixin, ListView):
    model = CabinetTable
    template_name = 'hardwareapp/cabinet/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cabinets'
        context['table_columns'] = ['Sl', 'Team', 'Name', 'Brand', 'Model', 'Quantity', 'Assign', 'Remaining', 'Issue', 'Actions']
        context.update(inventory_list_extras(self.request, CabinetTable))
        return context


class CabinetListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = CabinetTable.objects.filter(is_delete=False)
        qs = apply_team_filter(qs, request)
        qs = qs.select_related('team')
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(Q(name__icontains=params['search_value']) | Q(brand__icontains=params['search_value']) | Q(model__icontains=params['search_value']) | Q(team__name__icontains=params['search_value']))
        records_filtered = qs.count()
        order_cols = ['id', 'team__name', 'name', 'brand', 'model', 'quantity', 'assign', 'remaining']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        issue_totals = _issue_totals_for_component('cabinet', page)
        can_view = request.user.has_perm('hardwareapp.view_cabinettable')
        can_edit = request.user.has_perm('hardwareapp.change_cabinettable')
        can_copy = request.user.has_perm('hardwareapp.add_cabinettable')
        can_delete = request.user.has_perm('hardwareapp.delete_cabinettable')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string('partials/cell_link_or_span.html', {'url_name': 'hardwareapp:cabinet_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view}, request=request)
            actions_cell = render_to_string('partials/row_actions.html', {'detail_url_name': 'hardwareapp:cabinet_detail', 'update_url_name': 'hardwareapp:cabinet_update', 'copy_url_name': 'hardwareapp:cabinet_copy', 'delete_url_name': 'hardwareapp:cabinet_delete', 'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete}, request=request)
            data.append([counter, _inventory_table_team_name(obj), name_cell, obj.brand or '', obj.model or '', obj.quantity, obj.assign, obj.remaining, issue_totals.get(obj.pk, 0), actions_cell])
        return JsonResponse({'draw': params['draw'], 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': data})


class CabinetDetailView(InventoryAssignedMachinesDetailMixin, AutoPermissionRequiredMixin, DetailView):
    model = CabinetTable

    template_name = 'hardwareapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        #  Fields for generic template
        context['fields'] = [
             {"label": "Team", "value": obj.team.name},
             {"label": "Name", "value": obj.name},
             {"label": "Brand", "value": obj.brand},
             {"label": "Model", "value": obj.model},
            {"label": "Quantity", "value": obj.quantity},
        ]

        #  Buttons (same pattern you used before)
        context['update_url'] = reverse('hardwareapp:cabinet_update', args=[obj.pk])
        context['copy_url'] = reverse('hardwareapp:cabinet_copy', args=[obj.pk])
        context['delete_url'] = reverse('hardwareapp:cabinet_delete', args=[obj.pk])
        context['list_url'] = reverse('hardwareapp:cabinet_list')

        #  Permissions
        context['can_edit'] = self.request.user.has_perm('hardwareapp.change_cabinettable')
        context['can_copy'] = self.request.user.has_perm('hardwareapp.add_cabinettable')
        context['can_delete'] = self.request.user.has_perm('hardwareapp.delete_cabinettable')

        return context


class CabinetCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = CabinetTable
    form_class = CabinetForm
    template_name = 'hardwareapp/cabinet/form.html'
    success_url = reverse_lazy('hardwareapp:cabinet_list')
    success_message = 'Cabinet created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Cabinet'
        return context


class CabinetUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CabinetTable
    form_class = CabinetForm
    template_name = 'hardwareapp/cabinet/form.html'
    success_url = reverse_lazy('hardwareapp:cabinet_list')
    context_object_name = 'object'
    success_message = 'Cabinet updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Cabinet'
        return context


class CabinetDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = CabinetTable
    template_name = 'hardwareapp/common-html/delete.html'

    success_url = reverse_lazy('hardwareapp:cabinet_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Cabinet'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'hardwareapp.delete_cabinet'
        )

        #  cancel button
        context['cancel_url'] = reverse('hardwareapp:cabinet_list')
        return context


class CabinetCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(CabinetTable, pk=pk)
        copy = CabinetTable(team=obj.team, name=f"{obj.name or ''} (Copy)".strip() or 'Cabinet (Copy)', brand=obj.brand, model=obj.model, quantity=obj.quantity, assign=obj.assign, remaining=obj.remaining)
        copy.save()
        messages.success(request, 'Cabinet copied.')
        return redirect('hardwareapp:cabinet_list')

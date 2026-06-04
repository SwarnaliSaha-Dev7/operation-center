from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum , Count , Q
from django.db.utils import ProgrammingError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from commonapp.global_filters import (
    SESSION_KEY_DASHBOARD_LOW_STOCK,
    apply_hardware_issue_filters,
    apply_inventory_date_range,
    apply_inventory_assignee_scope,
    apply_machine_filters,
    apply_ticket_filters,
    apply_user_list_filters,
    get_filter_params,
)
from hardwareissueapp.models import HardwareIssueTable
from ticketingapp.models import Ticket
from commonapp.mixin import AutoPermissionRequiredMixin
from memberapp.models import Team, User
from hardwareapp.models import (
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
    MachineTable
)

_COMPONENT_ANALYTICS_CONFIG = (
    ('processor', 'Processor', ProcessorTable, 'hardwareapp:processor_list'),
    ('ram', 'RAM', RAMTable, 'hardwareapp:ram_list'),
    ('ssd', 'SSD', SSDTable, 'hardwareapp:ssd_list'),
    ('motherboard', 'Motherboard', MotherboardTable, 'hardwareapp:motherboard_list'),
    ('power_supply', 'Power Supply', PowerSupplyTable, 'hardwareapp:power_supply_list'),
    ('cabinet', 'Cabinet', CabinetTable, 'hardwareapp:cabinet_list'),
    ('liquid_cooler', 'Liquid Cooler', LiquidCoolerTable, 'hardwareapp:liquid_cooler_list'),
    ('graphics_card', 'Graphics Card', GraphicsCardTable, 'hardwareapp:graphics_card_list'),
    ('hdd', 'HDD', HDDTable, 'hardwareapp:hdd_list'),
    ('ups', 'UPS', UPSTable, 'hardwareapp:ups_list'),
    ('monitor', 'Monitor', MonitorTable, 'hardwareapp:monitor_list'),
    ('keyboard', 'Keyboard', KeyboardTable, 'hardwareapp:keyboard_list'),
    ('mouse', 'Mouse', MouseTable, 'hardwareapp:mouse_list'),
    ('headphone', 'Headphone', HeadphoneTable, 'hardwareapp:headphone_list'),
    ('pentable', 'Pen Tablets', Pentable, 'hardwareapp:pentable_list'),
    ('speaker', 'Speaker', SpeakerTable, 'hardwareapp:speaker_list'),
    ('webcam', 'Webcam', WebcamTable, 'hardwareapp:webcam_list'),
)


def _safe_component_totals(qs):
    try:
        totals = qs.aggregate(
            total_stock=Sum('quantity'),
            total_assign=Sum('assign'),
            total_remain=Sum('remaining'),
            total_issue=Sum('issue'),
        )
    except ProgrammingError:
        totals = qs.aggregate(
            total_stock=Sum('quantity'),
            total_assign=Sum('assign'),
            total_remain=Sum('remaining'),
        )
        totals['total_issue'] = 0
    return totals


def _component_option_label(obj):
    """Format for component display in dashboard."""
    if obj is None:
        return '—'
    if not getattr(obj, 'brand', None):
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


def _user_can_view_model(user, model_class):
    """True if user may view list/detail for this model (Django auth view permission)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    meta = model_class._meta
    return user.has_perm(f'{meta.app_label}.view_{meta.model_name}')


def _component_config_for_user(user):
    """Subset of _COMPONENT_ANALYTICS_CONFIG for models the user may view."""
    return tuple(row for row in _COMPONENT_ANALYTICS_CONFIG if _user_can_view_model(user, row[2]))


def _dashboard_team_stats(team_id, threshold, component_config, request):
    """Return (by_component, low_stock_items) for a team (global date range applies to inventory rows)."""
    by_component = {}
    low_stock_items = []
    for key, label, model_class , url_name in component_config:
        base = model_class.objects.filter(is_delete=False)
        base = apply_inventory_assignee_scope(base, request)
        base = apply_inventory_date_range(base, request)
        qs = _safe_component_totals(base.filter(team_id=team_id))
        by_component[key] = {
            'label': label,
            'url': url_name,
            'total_stock': qs['total_stock'] or 0,
            'total_assign': qs['total_assign'] or 0,
            'total_remain': qs['total_remain'] or 0,
            'total_issue': qs['total_issue'] or 0,
        }
        for obj in base.filter(team_id=team_id, remaining__lte=threshold).select_related('team'):
            low_stock_items.append({
                'team_name': getattr(obj.team, 'name', '') or '—',
                'component_type': label,
                'name': _component_option_label(obj),
                'remaining': getattr(obj, 'remaining', 0),
            })
    return by_component, low_stock_items




@method_decorator(require_http_methods(['POST']), name='dispatch')
class DashboardLowStockUpdateView(LoginRequiredMixin, View):
    """Save low-stock alert threshold (dashboard only; separate from global filters)."""

    def post(self, request):
        raw = (request.POST.get('low_stock') or '').strip()
        try:
            v = int(raw)
        except ValueError:
            v = 5
        request.session[SESSION_KEY_DASHBOARD_LOW_STOCK] = max(0, v)
        request.session.modified = True
        return redirect(reverse('dashboardapp:Dashboard'))


class ComponentAnalyticsDashboardView(AutoPermissionRequiredMixin, View):
    """Component analytics dashboard: stock/assign/remain by component, low-stock alerts (uses global filters)."""

    def get(self, request):
        p = get_filter_params(request)
        low_stock_threshold = p['low_stock']
        user = request.user
        component_config = _component_config_for_user(user)
        teams = list(Team.objects.filter(is_delete=False).order_by('name'))
        team_stats = {}
        all_low_stock = []

        for team in teams:
            by_comp, low_stock = _dashboard_team_stats(team.pk, low_stock_threshold, component_config, request)
            team_stats[team.pk] = {
                'team': team,
                'by_component': by_comp,
                'low_stock': low_stock,
            }
            all_low_stock.extend(low_stock)
        all_teams_by_component = {}
        for key, label, model_class, url_name in component_config:
            inv = model_class.objects.filter(is_delete=False)
            inv = apply_inventory_assignee_scope(inv, request)
            inv = apply_inventory_date_range(inv, request)
            qs = _safe_component_totals(inv)
            all_teams_by_component[key] = {
                'label': label,
                'url': url_name,
                'total_stock': qs['total_stock'] or 0,
                'total_assign': qs['total_assign'] or 0,
                'total_remain': qs['total_remain'] or 0,
                'total_issue': qs['total_issue'] or 0,
            }
        all_teams_rows = [
            (
                key,
                all_teams_by_component[key]['label'],
                all_teams_by_component[key]['total_stock'],
                all_teams_by_component[key]['total_assign'],
                all_teams_by_component[key]['total_remain'],
                all_teams_by_component[key]['total_issue'],
                all_teams_by_component[key]['url'],
            )
            for key, _, _, _ in component_config
        ]

        if p['team_id']:
            ts = team_stats.get(p['team_id'])
            if ts:
                by_comp = ts['by_component']
                dashboard_inventory_rows = [
                    (
                        key,
                        by_comp[key]['label'],
                        by_comp[key]['total_stock'],
                        by_comp[key]['total_assign'],
                        by_comp[key]['total_remain'],
                        by_comp[key]['total_issue'],
                        by_comp[key]['url'],
                    )
                    for key, _, _, _ in component_config
                ]
            else:
                dashboard_inventory_rows = []
        else:
            dashboard_inventory_rows = all_teams_rows

        if _user_can_view_model(user, MachineTable):
            machines = MachineTable.objects.filter(is_delete=False)
            machines = apply_machine_filters(machines, request)
        else:
            machines = MachineTable.objects.none()

        if _user_can_view_model(user, User):
            uq = User.objects.all()
            uq = apply_user_list_filters(uq, request)
            all_employee = uq.aggregate(total_employe=Count('id'))
        else:
            all_employee = {'total_employe': 0}

        if _user_can_view_model(user, MachineTable):
            all_machine_states = machines.aggregate(
                total_machine=Count('id'),
                machine_assigne=Count('id', filter=Q(member__isnull=False)),
                reamain=Count('id', filter=Q(member__isnull=True)),
            )
        else:
            all_machine_states = {'total_machine': 0, 'machine_assigne': 0, 'reamain': 0}

        hardware_issue_total = 0
        if _user_can_view_model(user, HardwareIssueTable):
            hardware_issue_total = apply_hardware_issue_filters(
                HardwareIssueTable.objects.all(), request
            ).count()

        it_ticket_total = 0
        if _user_can_view_model(user, Ticket):
            it_ticket_total = apply_ticket_filters(Ticket.objects.all(), request).count()

        dashboard_cards = []
        if _user_can_view_model(user, User):
            dashboard_cards.append(
                {
                    "label": "Total Employees",
                    "value": all_employee['total_employe'] or 0,
                    "color": " group bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 text-blue-700 hover:from-blue-100 hover:to-blue-200 hover:shadow-xl hover:border-blue-300",
                    "icon": 
                    """
                    <svg viewBox="-2 0 32 32" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="#053c85" stroke="#053c85" stroke-width="1.376"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g id="icomoon-ignore"> </g> <path d="M0 21.997c0 0.459 0 1.82 0 2.12s0.178 0.813 0.822 0.813c0.494 0 4.438 0 6.245 0 0.547 0 0.9 0 0.9 0h0.155c0 0 0.104 0 0.271 0 0 0.484 0 0.924 0 1.093 0 0.371 0.22 1.006 1.017 1.006 0.612 0 5.509 0 7.746 0 0.677 0 1.116 0 1.116 0h0.192c0 0 0.43 0 1.097 0 2.229 0 7.134 0 7.747 0 0.796 0 1.017-0.634 1.017-1.006s0-2.055 0-2.623-0.201-1.198-1.017-1.548c-1.032-0.452-3.799-1.452-5.537-1.965-0.134-0.043-0.157-0.050-0.157-0.646 0-0.642 0.074-1.097 0.23-1.431 0.215-0.456 0.469-1.224 0.559-1.912 0.256-0.296 0.603-0.88 0.826-1.993 0.197-0.981 0.105-1.338-0.025-1.673-0.014-0.035-0.029-0.070-0.039-0.11-0.048-0.225 0.018-1.42 0.188-2.348 0.116-0.636-0.030-1.988-0.906-3.108-0.553-0.707-1.612-1.576-3.513-1.695l-1.060-0.001c-1.933 0.121-2.991 0.989-3.544 1.696-0.876 1.119-1.021 2.472-0.905 3.108 0.168 0.927 0.236 2.122 0.186 2.352-0.010 0.035-0.025 0.070-0.038 0.105-0.13 0.335-0.221 0.692-0.026 1.673 0.223 1.113 0.571 1.697 0.826 1.993 0.091 0.688 0.345 1.456 0.559 1.912 0.198 0.42 0.4 0.916 0.4 1.409 0 0.597-0.023 0.604-0.166 0.649-0.358 0.105-0.763 0.232-1.189 0.368-1.004-0.373-2.267-0.809-3.183-1.080-0.109-0.034-0.127-0.040-0.127-0.522 0-0.519 0.060-0.887 0.186-1.157 0.174-0.369 0.379-0.989 0.453-1.546 0.206-0.239 0.487-0.711 0.667-1.611 0.159-0.793 0.084-1.081-0.021-1.352-0.011-0.029-0.023-0.057-0.031-0.089-0.039-0.182 0.014-1.148 0.15-1.898 0.093-0.514-0.023-1.607-0.731-2.513-0.447-0.571-1.303-1.273-2.838-1.371h-0.856c-1.562 0.097-2.417 0.8-2.864 1.371-0.708 0.906-0.826 1.999-0.731 2.513 0.135 0.75 0.191 1.716 0.151 1.902-0.008 0.028-0.021 0.056-0.031 0.085-0.106 0.271-0.179 0.559-0.021 1.352 0.18 0.9 0.461 1.372 0.667 1.611 0.074 0.557 0.279 1.176 0.452 1.546 0.16 0.34 0.324 0.741 0.324 1.139 0 0.483-0.018 0.488-0.134 0.525-1.358 0.401-3.553 1.163-4.482 1.552-0.66 0.283-0.976 0.845-0.976 1.304zM9.441 23.401c0-0.156 0.156-0.47 0.574-0.649 1.103-0.461 3.806-1.393 5.448-1.877 0.918-0.288 0.918-1.078 0.918-1.655 0-0.699-0.253-1.33-0.501-1.856-0.171-0.366-0.391-1.025-0.468-1.603l-0.041-0.31-0.205-0.237c-0.113-0.131-0.397-0.541-0.591-1.515-0.152-0.761-0.085-0.934-0.026-1.087l0.001-0.002 0.009-0.026c0.022-0.054 0.041-0.108 0.056-0.161l0.011-0.038 0.008-0.039c0.107-0.501-0.033-1.945-0.18-2.758-0.067-0.366 0.017-1.402 0.7-2.275 0.607-0.776 1.533-1.211 2.752-1.294l0.993 0.001c1.493 0.102 2.303 0.758 2.721 1.293 0.683 0.873 0.766 1.909 0.7 2.273-0.144 0.793-0.287 2.26-0.181 2.755l0.005 0.022 0.006 0.022c0.022 0.085 0.049 0.161 0.080 0.237 0.054 0.141 0.122 0.317-0.030 1.076-0.195 0.975-0.478 1.383-0.591 1.513l-0.206 0.238-0.040 0.312c-0.077 0.579-0.296 1.235-0.469 1.601-0.225 0.481-0.33 1.077-0.33 1.878 0 0.576 0 1.364 0.888 1.646 1.692 0.5 4.44 1.491 5.434 1.926 0.296 0.127 0.389 0.269 0.389 0.587v2.579h-17.828l-0.005-2.579zM1.049 21.997c0.002-0.041 0.067-0.222 0.341-0.34 0.899-0.377 3.066-1.126 4.365-1.51 0.886-0.282 0.886-1.064 0.886-1.531 0-0.603-0.214-1.14-0.424-1.586-0.136-0.291-0.304-0.811-0.361-1.237l-0.041-0.31-0.204-0.237c-0.064-0.073-0.281-0.372-0.433-1.133-0.112-0.557-0.067-0.673-0.031-0.766l0.006-0.014 0.004-0.014c0.022-0.054 0.036-0.097 0.048-0.14l0.012-0.039 0.008-0.039c0.103-0.484-0.045-1.763-0.144-2.309-0.046-0.257 0.022-1.034 0.527-1.68 0.453-0.578 1.149-0.904 2.071-0.968h0.788c1.127 0.080 1.734 0.569 2.046 0.968 0.504 0.645 0.573 1.424 0.527 1.68-0.106 0.577-0.244 1.841-0.146 2.304l0.005 0.022 0.005 0.022c0.020 0.074 0.043 0.14 0.069 0.207 0.036 0.092 0.081 0.21-0.030 0.766-0.153 0.762-0.37 1.059-0.433 1.132l-0.204 0.237-0.041 0.31c-0.057 0.428-0.225 0.947-0.363 1.238-0.195 0.417-0.286 0.926-0.286 1.603 0 0.468 0 1.251 0.859 1.523 0.543 0.161 1.219 0.383 1.887 0.616-1.103 0.378-2.155 0.761-2.763 1.015-0.818 0.351-1.209 1.045-1.209 1.613 0 0.118 0 0.287 0 0.481h-7.343v-1.884z" fill="#053c85"> </path> </g></svg>
                    """,
                    "url": "memberapp:member_list",
                }
            )
        if _user_can_view_model(user, MachineTable):
            dashboard_cards.extend([
                {
                    "label": "Total Machines",
                    "value": all_machine_states['total_machine'] or 0, 
                    "url": "hardwareapp:machine_list",
                    "icon": 
                    """
                    <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" fill="#0a5809" stroke="#0a5809" stroke-width="35.839999999999996"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><rect x="80" y="80" width="352" height="352" rx="48" ry="48" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linejoin:round;stroke-width:32px"&gt;</rect><rect x="144" y="144" width="224" height="224" rx="16" ry="16" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linejoin:round;stroke-width:32px"&gt;</rect><line x1="256" y1="80" x2="256" y2="48" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="336" y1="80" x2="336" y2="48" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="176" y1="80" x2="176" y2="48" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="256" y1="464" x2="256" y2="432" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="336" y1="464" x2="336" y2="432" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="176" y1="464" x2="176" y2="432" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="432" y1="256" x2="464" y2="256" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="432" y1="336" x2="464" y2="336" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="432" y1="176" x2="464" y2="176" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="48" y1="256" x2="80" y2="256" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="48" y1="336" x2="80" y2="336" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line><line x1="48" y1="176" x2="80" y2="176" style="fill:none;stroke:&lt;svg fill=" #0a5809"="" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" stroke="#0a5809"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><title>ionicons-v5-l</title><path d="M352,128H160a32,32,0,0,0-32,32V352a32,32,0,0,0,32,32H352a32,32,0,0,0,32-32V160A32,32,0,0,0,352,128Zm0,216a8,8,0,0,1-8,8H168a8,8,0,0,1-8-8V168a8,8,0,0,1,8-8H344a8,8,0,0,1,8,8Z" style="fill:none"></path><rect x="160" y="160" width="192" height="192" rx="8" ry="8"></rect><path d="M464,192a16,16,0,0,0,0-32H448V128a64.07,64.07,0,0,0-64-64H352V48a16,16,0,0,0-32,0V64H272V48a16,16,0,0,0-32,0V64H192V48a16,16,0,0,0-32,0V64H128a64.07,64.07,0,0,0-64,64v32H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v48H48a16,16,0,0,0,0,32H64v32a64.07,64.07,0,0,0,64,64h32v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h48v16a16,16,0,0,0,32,0V448h32a64.07,64.07,0,0,0,64-64V352h16a16,16,0,0,0,0-32H448V272h16a16,16,0,0,0,0-32H448V192ZM384,352a32,32,0,0,1-32,32H160a32,32,0,0,1-32-32V160a32,32,0,0,1,32-32H352a32,32,0,0,1,32,32Z"></path></g>;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px"&gt;</line></g></svg>
                    """
                    ,
                    "color": "group bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-200 text-green-700 hover:from-green-100 hover:to-green-200 hover:shadow-xl hover:border-green-300",
                    
                },
                {
                    "label": "Assigned Machines",
                    "value": all_machine_states['machine_assigne'] or 0,
                    "color": "bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-200 text-purple-700 hover:from-purple-100 hover:to-purple-200 hover:shadow-xl hover:border-purple-300",
                    "icon": 
                    """
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M9 12H4.6C4.03995 12 3.75992 12 3.54601 12.109C3.35785 12.2049 3.20487 12.3578 3.10899 12.546C3 12.7599 3 13.0399 3 13.6V19.4C3 19.9601 3 20.2401 3.10899 20.454C3.20487 20.6422 3.35785 20.7951 3.54601 20.891C3.75992 21 4.03995 21 4.6 21H9M9 21H15M9 21L9 8.6C9 8.03995 9 7.75992 9.10899 7.54601C9.20487 7.35785 9.35785 7.20487 9.54601 7.10899C9.75992 7 10.0399 7 10.6 7H13.4C13.9601 7 14.2401 7 14.454 7.10899C14.6422 7.20487 14.7951 7.35785 14.891 7.54601C15 7.75992 15 8.03995 15 8.6V21M15 21H19.4C19.9601 21 20.2401 21 20.454 20.891C20.6422 20.7951 20.7951 20.6422 20.891 20.454C21 20.2401 21 19.9601 21 19.4V4.6C21 4.03995 21 3.75992 20.891 3.54601C20.7951 3.35785 20.6422 3.20487 20.454 3.10899C20.2401 3 19.9601 3 19.4 3H16.6C16.0399 3 15.7599 3 15.546 3.10899C15.3578 3.20487 15.2049 3.35785 15.109 3.54601C15 3.75992 15 4.03995 15 4.6V8" stroke="#740671" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
                    """,
                "url": "hardwareapp:machine_list",
                },
                {
                    "label": "Remaining Machines",
                    "value": all_machine_states['reamain'] or 0,
                    "url": "hardwareapp:machine_list",
                    "color": "bg-gradient-to-br from-yellow-50 to-yellow-100 border-2 border-yellow-200 text-yellow-700 hover:from-yellow-100 hover:to-yellow-200 hover:shadow-xl hover:border-yellow-300",
                    "icon": 
                    """
                    <svg fill="#a38800" viewBox="0 0 64 64" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" xmlns:serif="http://www.serif.com/" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;" stroke="#a38800" stroke-width="1.3439999999999999"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.128"></g><g id="SVGRepo_iconCarrier"> <rect id="Icons" x="-640" y="-64" width="1280" height="800" style="fill:none;"></rect> <g id="Icons1" serif:id="Icons"> <g id="Strike"> </g> <g id="H1"> </g> <g id="H2"> </g> <g id="H3"> </g> <g id="list-ul"> </g> <g id="hamburger-1"> </g> <g id="hamburger-2"> </g> <g id="list-ol"> </g> <g id="list-task"> </g> <g id="trash"> </g> <g id="vertical-menu"> </g> <g id="horizontal-menu"> </g> <g id="sidebar-2"> </g> <g id="Pen"> </g> <g id="Pen1" serif:id="Pen"> </g> <g id="clock"> </g> <g id="external-link"> </g> <g id="hr"> </g> <g id="info"> </g> <g id="warning"> <path d="M32.427,7.987c2.183,0.124 4,1.165 5.096,3.281l17.936,36.208c1.739,3.66 -0.954,8.585 -5.373,8.656l-36.119,0c-4.022,-0.064 -7.322,-4.631 -5.352,-8.696l18.271,-36.207c0.342,-0.65 0.498,-0.838 0.793,-1.179c1.186,-1.375 2.483,-2.111 4.748,-2.063Zm-0.295,3.997c-0.687,0.034 -1.316,0.419 -1.659,1.017c-6.312,11.979 -12.397,24.081 -18.301,36.267c-0.546,1.225 0.391,2.797 1.762,2.863c12.06,0.195 24.125,0.195 36.185,0c1.325,-0.064 2.321,-1.584 1.769,-2.85c-5.793,-12.184 -11.765,-24.286 -17.966,-36.267c-0.366,-0.651 -0.903,-1.042 -1.79,-1.03Z" style="fill-rule:nonzero;"></path> <path d="M33.631,40.581l-3.348,0l-0.368,-16.449l4.1,0l-0.384,16.449Zm-3.828,5.03c0,-0.609 0.197,-1.113 0.592,-1.514c0.396,-0.4 0.935,-0.601 1.618,-0.601c0.684,0 1.223,0.201 1.618,0.601c0.395,0.401 0.593,0.905 0.593,1.514c0,0.587 -0.193,1.078 -0.577,1.473c-0.385,0.395 -0.929,0.593 -1.634,0.593c-0.705,0 -1.249,-0.198 -1.634,-0.593c-0.384,-0.395 -0.576,-0.886 -0.576,-1.473Z" style="fill-rule:nonzero;"></path> </g> <g id="plus-circle"> </g> <g id="minus-circle"> </g> <g id="vue"> </g> <g id="cog"> </g> <g id="logo"> </g> <g id="radio-check"> </g> <g id="eye-slash"> </g> <g id="eye"> </g> <g id="toggle-off"> </g> <g id="shredder"> </g> <g id="spinner--loading--dots-" serif:id="spinner [loading, dots]"> </g> <g id="react"> </g> <g id="check-selected"> </g> <g id="turn-off"> </g> <g id="code-block"> </g> <g id="user"> </g> <g id="coffee-bean"> </g> <g id="coffee-beans"> <g id="coffee-bean1" serif:id="coffee-bean"> </g> </g> <g id="coffee-bean-filled"> </g> <g id="coffee-beans-filled"> <g id="coffee-bean2" serif:id="coffee-bean"> </g> </g> <g id="clipboard"> </g> <g id="clipboard-paste"> </g> <g id="clipboard-copy"> </g> <g id="Layer1"> </g> </g> </g></svg>
                    """
                    ,
                }
                
                ])
        if _user_can_view_model(user, HardwareIssueTable):
            dashboard_cards.append(
                {
                    "label": "Hardware issues",
                    "value": hardware_issue_total,
                    "color": (
                        "group bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 "
                        "text-amber-900 hover:from-amber-100 hover:to-orange-100 hover:shadow-xl hover:border-amber-300"
                    ),
                    "icon": """
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#c2410c" stroke-width="2" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
                        </svg>
                    """,
                    "url": "hardwareissueapp:issue_list",
                }
            )
        if _user_can_view_model(user, Ticket):
            dashboard_cards.append(
                {
                    "label": "IT tickets",
                    "value": it_ticket_total,
                    "color": (
                        "group bg-gradient-to-br from-sky-50 to-cyan-50 border-2 border-sky-200 "
                        "text-sky-900 hover:from-sky-100 hover:to-cyan-100 hover:shadow-xl hover:border-sky-300"
                    ),
                    "icon": """
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#0369a1" stroke-width="2" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/>
                        </svg>
                    """,
                    "url": "ticketingapp:ticket_list",
                }
            )

        ctx = {
            'title': 'Dashboard',
            'teams': teams,
            'team_stats': team_stats,
            'all_teams_rows': all_teams_rows,
            'dashboard_inventory_rows': dashboard_inventory_rows,
            'all_low_stock': sorted(all_low_stock, key=lambda x: (x['component_type'], -x['remaining'])),
            'low_stock_threshold': low_stock_threshold,
            'dashboard_cards': dashboard_cards,
            'dashboard_has_inventory': bool(component_config),
            'gf_date_from': p['date_from'],
            'gf_date_to': p['date_to'],
            'gf_team_id': p['team_id'],
        }
        if request.GET.get('_fragment') == '1':
            return render(request, 'dashboardapp/dashboard_fragment.html', ctx)
        return render(request, 'dashboardapp/dashboard.html', ctx)

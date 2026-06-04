"""Summary cards and team filter context for hardware list pages."""
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.db.utils import ProgrammingError

from commonapp.global_filters import (
    apply_inventory_assignee_scope,
    apply_inventory_date_range,
    apply_inventory_filters,
    apply_machine_filters,
    get_filter_params,
)
from memberapp.models import Team

from hardwareapp.models import MachineTable, OperatingSystemTable


def team_id_from_request(request):
    return get_filter_params(request)['team_id']


def apply_team_filter(qs, request):
    """Backward-compatible name: inventory lists filter by team from global panel."""
    return apply_inventory_filters(qs, request)


def inventory_summary_cards(qs):
    """Totals from quantity / remaining / assign / issue fields."""
    try:
        agg = qs.aggregate(
            total=Coalesce(Sum('quantity'), 0),
            available=Coalesce(Sum('remaining'), 0),
            assigned=Coalesce(Sum('assign'), 0),
            issued=Coalesce(Sum('issue'), 0),
        )
    except ProgrammingError:
        agg = qs.aggregate(
            total=Coalesce(Sum('quantity'), 0),
            available=Coalesce(Sum('remaining'), 0),
            assigned=Coalesce(Sum('assign'), 0),
        )
        agg['issued'] = 0
    return [
        {
            'label': 'Total stock',
            'value': int(agg['total']),
            'color': 'bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200',
        },
        {
            'label': 'Available',
            'value': int(agg['available']),
            'color': 'bg-gradient-to-br from-emerald-50 to-teal-100 border border-emerald-200',
        },
        {
            'label': 'Assigned',
            'value': int(agg['assigned']),
            'color': 'bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200',
        },
        {
            'label': 'Issue',
            'value': int(agg['issued']),
            'color': 'bg-gradient-to-br from-red-50 to-rose-100 border border-red-200',
        },
    ]


def machine_summary_cards(qs):
    total = qs.count()
    unassigned = qs.filter(member__isnull=True).count()
    in_use = qs.filter(member__isnull=False).count()
    incomplete = qs.filter(
        Q(name__isnull=True) | Q(name='') | Q(code__isnull=True) | Q(code='')
    ).count()
    return [
        {
            'label': 'Total machines',
            'value': total,
            'color': 'bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200',
        },
        {
            'label': 'Unassigned',
            'value': unassigned,
            'color': 'bg-gradient-to-br from-emerald-50 to-teal-100 border border-emerald-200',
        },
        {
            'label': 'In use',
            'value': in_use,
            'color': 'bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200',
        },
        {
            'label': 'Incomplete records',
            'value': incomplete,
            'color': 'bg-gradient-to-br from-red-50 to-rose-100 border border-red-200',
        },
    ]


def os_summary_cards(qs):
    total = qs.count()
    linked = qs.annotate(_mc=Count('machines')).filter(_mc__gt=0).count()
    not_linked = max(0, total - linked)
    missing_name = qs.filter(Q(name__isnull=True) | Q(name='')).count()
    return [
        {
            'label': 'Total OS entries',
            'value': total,
            'color': 'bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200',
        },
        {
            'label': 'Linked to machines',
            'value': linked,
            'color': 'bg-gradient-to-br from-emerald-50 to-teal-100 border border-emerald-200',
        },
        {
            'label': 'Not linked',
            'value': not_linked,
            'color': 'bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200',
        },
        {
            'label': 'Missing name',
            'value': missing_name,
            'color': 'bg-gradient-to-br from-red-50 to-rose-100 border border-red-200',
        },
    ]


def teams_context(request):
    return {
        'teams': Team.objects.filter(is_delete=False).order_by('name'),
        'selected_team_id': team_id_from_request(request),
        'show_team_filter': False,
    }


def inventory_list_extras(request, model_cls):
    qs = apply_team_filter(model_cls.objects.filter(is_delete=False), request)
    ctx = teams_context(request)
    ctx['summary_cards'] = inventory_summary_cards(qs)
    return ctx


def machine_list_extras(request):
    qs = apply_machine_filters(MachineTable.objects.filter(is_delete=False), request)
    ctx = teams_context(request)
    ctx['summary_cards'] = machine_summary_cards(qs)
    return ctx


def os_list_extras(request):
    qs = OperatingSystemTable.objects.filter(is_delete=False)
    qs = apply_inventory_assignee_scope(qs, request)
    qs = apply_inventory_date_range(qs, request)
    return {
        'teams': [],
        'selected_team_id': None,
        'show_team_filter': False,
        'summary_cards': os_summary_cards(qs),
    }

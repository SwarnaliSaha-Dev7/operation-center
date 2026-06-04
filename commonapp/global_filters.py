"""Shared GET/DataTables params for the global filter panel (team, org fields, date range)."""
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

SESSION_KEY_GLOBAL_FILTERS = 'global_filters'
# Low-stock alert threshold is dashboard-only (not part of global filter panel).
SESSION_KEY_DASHBOARD_LOW_STOCK = 'dashboard_low_stock'

_FILTER_KEYS = (
    'team',
    'department',
    'designation',
    'member',
    'date_preset',
    'date_from',
    'date_to',
)


def _parse_int(val):
    if val is None or val == '':
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip()[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_merged_filter_raw(request):
    """
    Merge session-stored global filters with request.GET (GET wins per key when present).
    Used for form defaults and for parsing effective filter params everywhere.
    """
    stored = request.session.get(SESSION_KEY_GLOBAL_FILTERS)
    if not isinstance(stored, dict):
        stored = {}
    out = {}
    for k in _FILTER_KEYS:
        if k in request.GET:
            v = request.GET.get(k)
            out[k] = '' if v is None else str(v).strip()
        elif k in stored:
            out[k] = str(stored[k]).strip() if stored[k] is not None else ''
        else:
            out[k] = ''
    return out


def save_global_filters_from_post(request):
    """Persist filter form POST body to session (stateful global filters)."""
    data = {}
    for k in _FILTER_KEYS:
        data[k] = (request.POST.get(k) or '').strip()
    request.session[SESSION_KEY_GLOBAL_FILTERS] = data
    request.session.modified = True


def clear_global_filters(request):
    request.session.pop(SESSION_KEY_GLOBAL_FILTERS, None)
    request.session.modified = True


def get_dashboard_low_stock_threshold(request):
    """
    Threshold for dashboard low-stock highlighting only.
    GET ?low_stock= overrides for the current request; session stores the saved value from the dashboard form.
    """
    v = _parse_int(request.GET.get('low_stock'))
    if v is not None:
        return max(0, v)
    v = _parse_int(request.session.get(SESSION_KEY_DASHBOARD_LOW_STOCK))
    if v is not None:
        return max(0, v)
    return 5


def get_filter_params(request):
    """
    Effective global filters: session merged with GET, then parsed (dates, team, etc.).
    """
    g = get_merged_filter_raw(request)
    team_id = _parse_int(g.get('team') or g.get('team_id'))
    department_id = _parse_int(g.get('department'))
    designation_id = _parse_int(g.get('designation'))
    member_id = _parse_int(g.get('member'))
    low_stock = get_dashboard_low_stock_threshold(request)

    date_preset = (g.get('date_preset') or '').strip()
    date_from = _parse_date(g.get('date_from'))
    date_to = _parse_date(g.get('date_to'))

    today = timezone.localdate()
    if date_preset in ('3', '7', '15', '30', '180'):
        days = int(date_preset)
        date_from = today - timedelta(days=days - 1)
        date_to = today
    elif date_preset == 'custom' and date_from and date_to:
        pass
    elif date_from and date_to:
        pass
    else:
        date_from = None
        date_to = None

    return {
        'team_id': team_id,
        'department_id': department_id,
        'designation_id': designation_id,
        'member_id': member_id,
        'low_stock': low_stock,
        'date_from': date_from,
        'date_to': date_to,
        'date_preset': date_preset,
    }


def apply_inventory_date_range(qs, request):
    """Restrict inventory rows to created_at within the global filter date range (if set)."""
    p = get_filter_params(request)
    if p['date_from'] and p['date_to']:
        return qs.filter(created_at__date__gte=p['date_from'], created_at__date__lte=p['date_to'])
    return qs


def apply_inventory_assignee_scope(qs, request):
    """
    Inventory/OS rows are scoped to machines: narrow by assignee's member, department,
    and designation (ANDed when multiple are set). Uses `machines` reverse M2M on component models.
    """
    p = get_filter_params(request)
    if p['member_id'] is not None:
        qs = qs.filter(machines__member_id=p['member_id'])
    if p['department_id'] is not None:
        qs = qs.filter(machines__member__department_id=p['department_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(machines__member__designation_id=p['designation_id'])
    return qs.distinct()


def apply_inventory_filters(qs, request):
    """Component inventory: team on row, assignee scope (member/dept/designation via machines), date range."""
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(team_id=p['team_id'])
    qs = apply_inventory_assignee_scope(qs, request)
    return apply_inventory_date_range(qs, request)


def apply_machine_filters(qs, request):
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(team_id=p['team_id'])
    if p['department_id'] is not None:
        qs = qs.filter(department_id=p['department_id'])
    if p['member_id'] is not None:
        qs = qs.filter(member_id=p['member_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(member__designation_id=p['designation_id'])
    if p['date_from'] and p['date_to']:
        qs = qs.filter(created_at__date__gte=p['date_from'], created_at__date__lte=p['date_to'])
    return qs


def apply_user_list_filters(qs, request):
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(team_id=p['team_id'])
    if p['department_id'] is not None:
        qs = qs.filter(department_id=p['department_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(designation_id=p['designation_id'])
    if p['member_id'] is not None:
        qs = qs.filter(pk=p['member_id'])
    if p['date_from'] and p['date_to']:
        qs = qs.filter(date_joined__date__gte=p['date_from'], date_joined__date__lte=p['date_to'])
    return qs


def apply_hardware_issue_filters(qs, request):
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(team_id=p['team_id'])
    if p['member_id'] is not None:
        qs = qs.filter(issued_by_id=p['member_id'])
    if p['department_id'] is not None:
        qs = qs.filter(issued_by__department_id=p['department_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(issued_by__designation_id=p['designation_id'])
    if p['date_from'] and p['date_to']:
        qs = qs.filter(created_at__date__gte=p['date_from'], created_at__date__lte=p['date_to'])
    return qs


def apply_ticket_filters(qs, request):
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(createdby__team_id=p['team_id'])
    if p['department_id'] is not None:
        qs = qs.filter(createdby__department_id=p['department_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(createdby__designation_id=p['designation_id'])
    if p['member_id'] is not None:
        qs = qs.filter(Q(assigned_to_id=p['member_id']) | Q(createdby_id=p['member_id']))
    if p['date_from'] and p['date_to']:
        qs = qs.filter(created_at__date__gte=p['date_from'], created_at__date__lte=p['date_to'])
    return qs


def apply_master_created_date_range(qs, request):
    """CreatedUpdatedByMixin rows: filter by global reporting period."""
    p = get_filter_params(request)
    if p['date_from'] and p['date_to']:
        return qs.filter(created_at__date__gte=p['date_from'], created_at__date__lte=p['date_to'])
    return qs


def apply_team_list_global_filters(qs, request):
    """Team catalog list: respect global scope (team / org / member) + date range."""
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(pk=p['team_id'])
    elif p['department_id'] is not None:
        qs = qs.filter(members__department_id=p['department_id']).distinct()
    elif p['designation_id'] is not None:
        qs = qs.filter(members__designation_id=p['designation_id']).distinct()
    elif p['member_id'] is not None:
        qs = qs.filter(members__pk=p['member_id']).distinct()
    return apply_master_created_date_range(qs, request)


def apply_department_list_global_filters(qs, request):
    """Department catalog list."""
    p = get_filter_params(request)
    if p['department_id'] is not None:
        qs = qs.filter(pk=p['department_id'])
    elif p['member_id'] is not None:
        qs = qs.filter(members__pk=p['member_id']).distinct()
    elif p['team_id'] is not None:
        qs = qs.filter(members__team_id=p['team_id']).distinct()
    return apply_master_created_date_range(qs, request)


def apply_designation_list_global_filters(qs, request):
    """Designation catalog list."""
    p = get_filter_params(request)
    if p['designation_id'] is not None:
        qs = qs.filter(pk=p['designation_id'])
    elif p['member_id'] is not None:
        qs = qs.filter(members__pk=p['member_id']).distinct()
    elif p['team_id'] is not None:
        qs = qs.filter(members__team_id=p['team_id']).distinct()
    return apply_master_created_date_range(qs, request)


def apply_role_list_global_filters(qs, request):
    """Auth Group list: scope groups that have at least one matching member."""
    p = get_filter_params(request)
    if p['team_id'] is not None:
        qs = qs.filter(user__team_id=p['team_id'])
    if p['department_id'] is not None:
        qs = qs.filter(user__department_id=p['department_id'])
    if p['designation_id'] is not None:
        qs = qs.filter(user__designation_id=p['designation_id'])
    if p['member_id'] is not None:
        qs = qs.filter(user__pk=p['member_id'])
    return qs.distinct()

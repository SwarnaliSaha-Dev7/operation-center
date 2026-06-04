from commonapp.global_filters import get_merged_filter_raw
from memberapp.models import Department, Designation, Team, User

# List pages where the global filter bar must not appear (filter stays active in session for other pages).
_GLOBAL_FILTER_EXCLUDED_LISTS = frozenset(
    {
        ('notificationapp', 'notification_list'),
        ('memberapp', 'team_list'),
        ('memberapp', 'department_list'),
        ('memberapp', 'member_list'),
    }
)


def should_show_global_filters(request):
    """True on dashboard and on list pages except notification, team, department, member lists."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return False
    match = getattr(request, 'resolver_match', None)
    if not match:
        return False
    app = getattr(match, 'app_name', '') or ''
    name = getattr(match, 'url_name', '') or ''

    if app == 'dashboardapp' and name == 'Dashboard':
        return True

    if (app, name) in _GLOBAL_FILTER_EXCLUDED_LISTS:
        return False

    if name.endswith('_list_data'):
        return False
    if name.endswith('_list'):
        return True

    return False


def global_filter_choices(request):
    empty = {
        'gf_teams': [],
        'gf_departments': [],
        'gf_designations': [],
        'gf_members': [],
        'gf': {},
        'show_global_filters': False,
    }
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return empty

    if not should_show_global_filters(request):
        return empty

    return {
        'gf_teams': Team.objects.filter(is_delete=False).order_by('name'),
        'gf_departments': Department.objects.filter(is_delete=False).order_by('name'),
        'gf_designations': Designation.objects.filter(is_delete=False).order_by('name'),
        'gf_members': User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        'gf': get_merged_filter_raw(request),
        'show_global_filters': True,
    }

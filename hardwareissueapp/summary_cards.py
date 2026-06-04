"""Summary metrics for hardware issue list header cards."""
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


def hardware_issue_summary_cards(qs):
    """Build four summary dicts for templates; qs should match the list (non-deleted issues)."""
    total = qs.count()
    units = qs.aggregate(u=Coalesce(Sum('quantity'), 0))['u']
    type_count = qs.values('component_type').distinct().count()
    now = timezone.now()
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = qs.filter(created_at__gte=start_month).count()
    return [
        {
            'label': 'Total issues',
            'value': total,
            'color': 'bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200',
        },
        {
            'label': 'Units issued',
            'value': int(units),
            'color': 'bg-gradient-to-br from-emerald-50 to-teal-100 border border-emerald-200',
        },
        {
            'label': 'This month',
            'value': this_month,
            'color': 'bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200',
        },
        {
            'label': 'Component types',
            'value': type_count,
            'color': 'bg-gradient-to-br from-rose-50 to-red-100 border border-rose-200',
        },
    ]

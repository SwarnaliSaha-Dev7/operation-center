"""Summary metrics for IT ticket list header cards (same scope as list queryset)."""
from django.db.models import Count

from ticketingapp.models import Ticket


def ticket_summary_cards(qs):
    """One card per ticket status; counts must match the filtered queryset (queue vs own tickets)."""
    by_status = {row['status']: row['c'] for row in qs.values('status').annotate(c=Count('id'))}
    specs = [
        (Ticket.Status.OPEN, 'Open'),
        (Ticket.Status.IN_PROGRESS, 'In progress'),
        (Ticket.Status.RESOLVED, 'Resolved'),
        (Ticket.Status.CLOSED, 'Closed'),
    ]
    colors = [
        'bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200',
        'bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200',
        'bg-gradient-to-br from-emerald-50 to-teal-100 border border-emerald-200',
        'bg-gradient-to-br from-slate-50 to-slate-200 border border-slate-300',
    ]
    return [
        {
            'label': label,
            'value': by_status.get(code, 0),
            'color': colors[i],
        }
        for i, (code, label) in enumerate(specs)
    ]

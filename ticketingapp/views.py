from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from commonapp.global_filters import apply_ticket_filters
from commonapp.mixin import AutoPermissionRequiredMixin
from commonapp.utils import get_datatables_params
from ticketingapp.forms import TicketCommentForm, TicketForm
from ticketingapp.models import Ticket, TicketComment
from ticketingapp.summary_cards import ticket_summary_cards
from ticketingapp.ticket_notifications import (
    notify_new_ticket,
    notify_ticket_closed,
    notify_ticket_comment,
    notify_ticket_reopened,
    notify_ticket_resolved,
    notify_ticket_taken,
)

User = get_user_model()

IT_PERM = 'ticketingapp.manage_it_tickets'


def member_is_it_staff(member):
    return member.is_superuser or member.has_perm(IT_PERM)


def member_can_access_ticket(member, ticket):
    if member_is_it_staff(member):
        return True
    return ticket.createdby_id == member.pk or ticket.assigned_to_id == member.pk


def member_can_edit_ticket(member, ticket):
    """Reporter can edit while open/in progress; IT can edit until closed."""
    if ticket.status == Ticket.Status.CLOSED:
        return False
    if not member_can_access_ticket(member, ticket):
        return False
    if member_is_it_staff(member):
        return True
    if ticket.createdby_id == member.pk and ticket.status in (
        Ticket.Status.OPEN,
        Ticket.Status.IN_PROGRESS,
    ):
        return True
    return False


def ticket_list_queryset(member):
    qs = Ticket.objects.filter(is_delete=False).select_related('createdby', 'assigned_to')
    if member_is_it_staff(member):
        return qs.order_by('-created_at')
    return qs.filter(Q(createdby=member) | Q(assigned_to=member)).order_by('-created_at')


_STATUS_BADGE_CLASS = {
    Ticket.Status.OPEN: 'bg-sky-100 text-sky-800',
    Ticket.Status.IN_PROGRESS: 'bg-amber-100 text-amber-900',
    Ticket.Status.RESOLVED: 'bg-emerald-100 text-emerald-800',
    Ticket.Status.CLOSED: 'bg-slate-200 text-slate-700',
}

_PRIORITY_BADGE_CLASS = {
    Ticket.Priority.LOW: 'bg-slate-100 text-slate-700 ring-1 ring-slate-200/80',
    Ticket.Priority.NORMAL: 'bg-sky-100 text-sky-900',
    Ticket.Priority.HIGH: 'bg-amber-100 text-amber-950 ring-1 ring-amber-200/90',
    Ticket.Priority.URGENT: 'bg-rose-100 text-rose-900 ring-1 ring-rose-200',
}


def _ticket_title_cell(ticket, can_view):
    if can_view:
        return format_html(
            '<a href="{}" class="font-medium text-indigo-700 hover:underline">{}</a>',
            reverse('ticketingapp:ticket_detail', args=[ticket.pk]),
            ticket.title,
        )
    return format_html('<span class="font-medium text-slate-800">{}</span>', ticket.title)


def _ticket_status_cell(ticket):
    css = _STATUS_BADGE_CLASS.get(ticket.status, 'bg-slate-200 text-slate-700')
    return format_html(
        '<span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        css,
        ticket.get_status_display(),
    )


def _ticket_priority_cell(ticket):
    css = _PRIORITY_BADGE_CLASS.get(ticket.priority, 'bg-slate-100 text-slate-700')
    return format_html(
        '<span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        css,
        ticket.get_priority_display(),
    )


class TicketListView(AutoPermissionRequiredMixin, ListView):
    model = Ticket
    template_name = 'ticketingapp/ticket/list.html'

    def get_queryset(self):
        return Ticket.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'IT tickets'
        ctx['member'] = self.request.user
        ctx['is_it_queue'] = member_is_it_staff(self.request.user)
        qs_tickets = apply_ticket_filters(ticket_list_queryset(self.request.user), self.request)
        ctx['summary_cards'] = ticket_summary_cards(qs_tickets)
        ctx['table_columns'] = [
            'Sl',
            'Ticket #',
            'Title',
            'Status',
            'Priority',
            'Member',
            'Assigned',
            'Created',
        ]
        return ctx


class TicketListDataView(AutoPermissionRequiredMixin, View):
    model = Ticket
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = ticket_list_queryset(request.user)
        qs = apply_ticket_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            sv = params['search_value']
            qs = qs.filter(
                Q(ticket_number__icontains=sv)
                | Q(title__icontains=sv)
                | Q(status__icontains=sv)
                | Q(priority__icontains=sv)
                | Q(category__icontains=sv)
                | Q(createdby__username__icontains=sv)
                | Q(createdby__first_name__icontains=sv)
                | Q(createdby__last_name__icontains=sv)
                | Q(assigned_to__username__icontains=sv)
                | Q(assigned_to__first_name__icontains=sv)
                | Q(assigned_to__last_name__icontains=sv)
            )
        records_filtered = qs.count()
        order_cols = [
            'id',
            'ticket_number',
            'title',
            'status',
            'priority',
            'createdby__username',
            'assigned_to__username',
            'created_at',
        ]
        if 0 <= params['order_column'] < len(order_cols):
            col = order_cols[params['order_column']]
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{col}')
        else:
            qs = qs.order_by('-created_at')
        page = qs[params['start'] : params['start'] + params['length']]
        can_view = request.user.has_perm('ticketingapp.view_ticket')
        data = []
        for idx, t in enumerate(page):
            counter = params['start'] + idx + 1
            createdby = (t.createdby.get_full_name() or '').strip() or (
                t.createdby.username if t.createdby else '—'
            )
            assigned = '—'
            if t.assigned_to_id:
                assigned = (t.assigned_to.get_full_name() or '').strip() or t.assigned_to.username
            created = t.created_at.strftime('%Y-%m-%d %H:%M')
            data.append(
                [
                    counter,
                    t.ticket_number,
                    _ticket_title_cell(t, can_view),
                    _ticket_status_cell(t),
                    _ticket_priority_cell(t),
                    createdby,
                    assigned,
                    created,
                ]
            )
        return JsonResponse(
            {
                'draw': params['draw'],
                'recordsTotal': records_total,
                'recordsFiltered': records_filtered,
                'data': data,
            }
        )


class TicketCreateView(AutoPermissionRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticketingapp/ticket/form.html'
    success_url = reverse_lazy('ticketingapp:ticket_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'New IT ticket'
        ctx['member'] = self.request.user
        ctx['is_edit'] = False
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Raising member (reporter); mixin audit fields may also apply when configured.
        self.object.createdby = self.request.user
        self.object.save()
        notify_new_ticket(self.object, self.request.user)
        messages.success(
            self.request,
            f'Ticket {self.object.ticket_number} submitted.',
        )
        return HttpResponseRedirect(self.get_success_url())


class TicketUpdateView(AutoPermissionRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticketingapp/ticket/form.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return Ticket.objects.filter(is_delete=False).select_related('createdby', 'assigned_to')

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        ticket = Ticket.objects.filter(pk=self.kwargs.get('pk'), is_delete=False).first()
        if not ticket:
            return False
        return member_can_edit_ticket(user, ticket)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit ticket {self.object.ticket_number}'
        ctx['member'] = self.request.user
        ctx['is_edit'] = True
        return ctx

    def get_success_url(self):
        return reverse('ticketingapp:ticket_detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, 'Ticket updated.')
        return super().form_valid(form)


class TicketDetailView(AutoPermissionRequiredMixin, DetailView):
    model = Ticket
    template_name = 'ticketingapp/ticket/detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return Ticket.objects.filter(is_delete=False).select_related('createdby', 'assigned_to')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not member_can_access_ticket(self.request.user, obj):
            raise PermissionDenied('You do not have access to this ticket.')
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        member = self.request.user
        ticket = self.object
        ctx['title'] = f'{ticket.ticket_number} · {ticket.title}'
        ctx['member'] = member
        qs = ticket.comments.select_related('author').order_by('created_at')
        if not member_is_it_staff(member):
            qs = qs.filter(is_internal=False)
        ctx['comments'] = qs
        ctx['comment_form'] = TicketCommentForm()
        ctx['can_manage'] = member_is_it_staff(member)
        ctx['can_act'] = member_can_access_ticket(member, ticket)
        ctx['list_url'] = reverse('ticketingapp:ticket_list')
        ctx['can_edit'] = member_can_edit_ticket(member, ticket)
        ctx['update_url'] = reverse('ticketingapp:ticket_update', args=[ticket.pk])
        return ctx


class TicketCommentPostView(AutoPermissionRequiredMixin, View):
    model = Ticket
    http_method_names = ['post']

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk, is_delete=False)
        if not member_can_access_ticket(request.user, ticket):
            raise PermissionDenied('You cannot comment on this ticket.')
        form = TicketCommentForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please enter a message.')
            return redirect('ticketingapp:ticket_detail', pk=pk)
        is_internal = form.cleaned_data.get('is_internal') and member_is_it_staff(request.user)
        body = form.cleaned_data['body'].strip()
        TicketComment.objects.create(
            ticket=ticket,
            author=request.user,
            body=body,
            is_internal=is_internal,
        )
        notify_ticket_comment(ticket, request.user, body, is_internal)
        messages.success(request, 'Comment added.')
        return redirect('ticketingapp:ticket_detail', pk=pk)


class TicketActionView(AutoPermissionRequiredMixin, View):
    model = Ticket
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk, is_delete=False)
        if not member_can_access_ticket(request.user, ticket):
            raise PermissionDenied('You cannot modify this ticket.')
        action = (request.POST.get('action') or '').strip()
        member = request.user
        it = member_is_it_staff(member)
        is_reporter = ticket.createdby_id == member.pk

        def save_t(msg):
            ticket.save()
            messages.success(request, msg)

        # Flow: Open → (IT: Take → In progress) → (IT: Resolve → Resolved) → (raising member: Close → Closed)
        if action == 'take' and it and ticket.status == Ticket.Status.OPEN:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.assigned_to = member
            save_t('You took this ticket; it is now in progress.')
            notify_ticket_taken(ticket, member)
        elif action == 'resolve' and it and ticket.status == Ticket.Status.IN_PROGRESS:
            ticket.status = Ticket.Status.RESOLVED
            save_t('Ticket marked resolved. The raising member can close it when satisfied.')
            notify_ticket_resolved(ticket, member)
        elif action == 'close':
            if is_reporter and ticket.status == Ticket.Status.RESOLVED:
                ticket.status = Ticket.Status.CLOSED
                save_t('Ticket closed.')
                notify_ticket_closed(ticket, member)
            elif ticket.status == Ticket.Status.CLOSED:
                messages.info(request, 'This ticket is already closed.')
            elif not is_reporter:
                messages.error(request, 'Only the member who raised the ticket can close it after it is resolved.')
            else:
                messages.error(request, 'You can close the ticket only after IT has marked it resolved.')
        elif action == 'reopen' and (it or is_reporter):
            if ticket.status in (Ticket.Status.CLOSED, Ticket.Status.RESOLVED):
                ticket.status = Ticket.Status.OPEN
                save_t('Ticket reopened.')
                notify_ticket_reopened(ticket, member)
            else:
                messages.error(request, 'Only resolved or closed tickets can be reopened.')
        else:
            messages.error(request, 'Invalid or not allowed action.')

        return redirect('ticketingapp:ticket_detail', pk=pk)

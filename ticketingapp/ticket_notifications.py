"""Create in-app notifications for ticket lifecycle events."""
from django.urls import reverse

from notificationapp.models import Notification
from notificationapp.services import get_users_with_permission, notify_user, notify_users


def _ticket_link(ticket):
    return reverse('ticketingapp:ticket_detail', args=[ticket.pk])


def notify_new_ticket(ticket, actor):
    recipients = get_users_with_permission('ticketingapp', 'manage_it_tickets').exclude(pk=actor.pk)
    actor_label = actor.get_full_name() or actor.username
    notify_users(
        recipients,
        f'New ticket {ticket.ticket_number}',
        f'{actor_label}: {ticket.title}',
        link_url=_ticket_link(ticket),
        category=Notification.Category.TICKET,
        actor=actor,
    )


def notify_ticket_comment(ticket, author, body_text, is_internal):
    if is_internal:
        return
    link = _ticket_link(ticket)
    author_label = author.get_full_name() or author.username
    preview = (body_text or '').strip()[:400]
    seen = set()
    for u in (ticket.createdby, ticket.assigned_to):
        if u is None or u.pk == author.pk or u.pk in seen:
            continue
        seen.add(u.pk)
        notify_user(
            u,
            f'Comment on ticket {ticket.ticket_number}',
            f'{author_label}: {preview}' if preview else f'{author_label} added a comment.',
            link_url=link,
            category=Notification.Category.TICKET,
            actor=author,
        )


def notify_ticket_taken(ticket, it_member):
    createdby = ticket.createdby
    if not createdby or createdby.pk == it_member.pk:
        return
    notify_user(
        createdby,
        f'Ticket {ticket.ticket_number} in progress',
        f'{it_member.get_full_name() or it_member.username} took your ticket.',
        link_url=_ticket_link(ticket),
        category=Notification.Category.TICKET,
        actor=it_member,
    )


def notify_ticket_resolved(ticket, it_member):
    createdby = ticket.createdby
    if not createdby:
        return
    notify_user(
        createdby,
        f'Ticket {ticket.ticket_number} resolved',
        'IT marked this ticket resolved. You can close it when satisfied.',
        link_url=_ticket_link(ticket),
        category=Notification.Category.TICKET,
        actor=it_member,
    )


def notify_ticket_closed(ticket, closed_by):
    assignee = ticket.assigned_to
    if not assignee or assignee.pk == closed_by.pk:
        return
    notify_user(
        assignee,
        f'Ticket {ticket.ticket_number} closed',
        f'{closed_by.get_full_name() or closed_by.username} closed the ticket.',
        link_url=_ticket_link(ticket),
        category=Notification.Category.TICKET,
        actor=closed_by,
    )


def notify_ticket_reopened(ticket, actor):
    recipients = get_users_with_permission('ticketingapp', 'manage_it_tickets').exclude(pk=actor.pk)
    label = actor.get_full_name() or actor.username
    notify_users(
        recipients,
        f'Ticket {ticket.ticket_number} reopened',
        f'{label} reopened the ticket.',
        link_url=_ticket_link(ticket),
        category=Notification.Category.TICKET,
        actor=actor,
    )

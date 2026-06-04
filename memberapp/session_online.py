"""Detect users with a non-expired browser session (logged in via OpsCenter in a browser)."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone


def logged_in_user_ids():
    """
    Return user PKs that currently have a **browser login**: a non-expired Django
    session whose store is the database (session cookie set at login).

    Not the same as "tab is open right now" — only that the session has not expired.
    Inactive accounts are excluded even if a stale session row exists.
    """
    engine = getattr(settings, 'SESSION_ENGINE', '') or ''
    if 'signed_cookies' in engine:
        # Auth lives only in the client cookie; django_session is not authoritative.
        return set()

    ids = set()
    now = timezone.now()
    qs = Session.objects.filter(expire_date__gte=now).only('session_data')
    for session in qs.iterator(chunk_size=500):
        try:
            data = session.get_decoded()
        except Exception:
            continue
        uid = data.get('_auth_user_id')
        if uid is None:
            continue
        try:
            ids.add(int(uid))
        except (TypeError, ValueError):
            continue

    if not ids:
        return set()

    User = get_user_model()
    return set(
        User.objects.filter(pk__in=ids, is_active=True).values_list('pk', flat=True)
    )

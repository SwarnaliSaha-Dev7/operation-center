"""Create in-app notifications for one or many recipients."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q

from notificationapp.models import Notification

User = get_user_model()


def get_users_with_permission(app_label: str, codename: str):
    """Active users with this permission (including superusers)."""
    try:
        perm = Permission.objects.get(
            codename=codename,
            content_type__app_label=app_label,
        )
    except Permission.DoesNotExist:
        return User.objects.filter(is_active=True, is_superuser=True)
    return (
        User.objects.filter(is_active=True)
        .filter(
            Q(is_superuser=True)
            | Q(groups__permissions=perm)
            | Q(user_permissions=perm)
        )
        .distinct()
    )


def notify_user(
    recipient,
    title: str,
    body: str = '',
    *,
    link_url: str = '',
    category: str = Notification.Category.GENERAL,
    actor=None,
):
    if not recipient or not recipient.is_active:
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        title=title[:255],
        body=body or '',
        link_url=(link_url or '')[:500],
        category=category,
    )


def notify_users(
    recipients,
    title: str,
    body: str = '',
    *,
    link_url: str = '',
    category: str = Notification.Category.GENERAL,
    actor=None,
):
    """Bulk-create the same notification for many recipients (skips inactive / duplicates in one batch)."""
    seen = set()
    rows = []
    for u in recipients:
        if not u or not u.is_active or u.pk in seen:
            continue
        seen.add(u.pk)
        rows.append(
            Notification(
                recipient=u,
                actor=actor,
                title=title[:255],
                body=body or '',
                link_url=(link_url or '')[:500],
                category=category,
            )
        )
    if not rows:
        return 0
    Notification.objects.bulk_create(rows)
    return len(rows)

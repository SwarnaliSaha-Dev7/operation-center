from notificationapp.models import Notification


def notification_badge(request):
    """Unread count and a few recent unread rows for the sidebar / shell."""
    if not request.user.is_authenticated:
        return {
            'notification_unread_count': 0,
            'notification_preview': [],
        }
    unread = Notification.objects.filter(
        recipient=request.user,
        read_at__isnull=True,
    ).order_by('-created_at')
    return {
        'notification_unread_count': unread.count(),
        'notification_preview': list(unread[:5]),
    }

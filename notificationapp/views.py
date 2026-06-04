from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from notificationapp.models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notificationapp/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 25

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related('actor')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Notifications'
        return ctx


class NotificationOpenView(LoginRequiredMixin, View):
    """Mark one notification read and redirect to its link (or notifications list)."""

    def get(self, request, pk):
        n = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if n.read_at is None:
            n.read_at = timezone.now()
            n.save(update_fields=['read_at'])
        target = (n.link_url or '').strip()
        if target.startswith('/') and not target.startswith('//'):
            return redirect(target)
        return redirect('notificationapp:notification_list')


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request):
        Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return redirect('notificationapp:notification_list')


class NotificationCountApiView(LoginRequiredMixin, View):
    """Lightweight JSON for optional badge polling."""

    def get(self, request):
        n = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return JsonResponse({'unread': n})

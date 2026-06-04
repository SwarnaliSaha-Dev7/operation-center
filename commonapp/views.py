from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView


def _safe_redirect_target(request, default_path):
    """POST `next` must be a same-origin relative path (open-redirect safe)."""
    cand = (request.POST.get('next') or '').strip() or default_path
    if cand.startswith('/') and not cand.startswith('//'):
        return cand
    return default_path


@method_decorator(require_http_methods(['POST']), name='dispatch')
class GlobalFilterApplyView(LoginRequiredMixin, View):
    """Persist global filter form to session and redirect back."""

    def post(self, request):
        from commonapp.global_filters import save_global_filters_from_post

        save_global_filters_from_post(request)
        default = reverse('dashboardapp:Dashboard')
        return redirect(_safe_redirect_target(request, default))


@method_decorator(require_http_methods(['POST']), name='dispatch')
class GlobalFilterClearView(LoginRequiredMixin, View):
    """Clear session global filters and redirect back."""

    def post(self, request):
        from commonapp.global_filters import clear_global_filters

        clear_global_filters(request)
        default = reverse('dashboardapp:Dashboard')
        return redirect(_safe_redirect_target(request, default))


class ForbiddenView(TemplateView):
    template_name = 'commonapp/forbidden.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Forbidden'
        return context

from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve, reverse


class AutoPermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Requires login, then checks Django model permission (add/change/delete/view) from URL and view model."""

    def _get_view_model(self):
        """Return the model class from the current view, or None."""
        resolved = resolve(self.request.path)
        view_class = getattr(resolved.func, "view_class", None)
        if not view_class:
            return None
        model = getattr(view_class, "model", None)
        if model:
            return model
        if hasattr(view_class, "get_queryset"):
            try:
                return view_class.get_queryset(self).model
            except AttributeError:
                pass
        return None

    def _path_action(self):
        """Return Django permission action from request path."""
        path = self.request.path
        if "/create/" in path or "/copy/" in path:
            return "add"
        if "/edit/" in path or "/update/" in path:
            return "change"
        if "/delete/" in path:
            return "delete"
        return "view"

    def _user_permission_codenames(self):
        """Yield permission strings (app_label.codename) for the current user."""
        user = self.request.user
        for perm in user.user_permissions.select_related("content_type"):
            yield f"{perm.content_type.app_label}.{perm.codename}"
        for group in user.groups.prefetch_related("permissions__content_type"):
            for perm in group.permissions.select_related("content_type"):
                yield f"{perm.content_type.app_label}.{perm.codename}"

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True

        model = self._get_view_model()
        if not model:
            return True

        meta = model._meta
        action = self._path_action()
        required = f"{meta.app_label}.{action}_{meta.model_name}"

        return required in set(self._user_permission_codenames())

    def handle_no_permission(self):
        request = self.request
        # For AJAX/DataTables: return JSON so browser doesn't get HTML (avoids MIME type mismatch)
        wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (getattr(request, "accepted_media_types", None) or [])
        if wants_json:
            try:
                login_url = reverse(settings.LOGIN_URL) if not settings.LOGIN_URL.startswith("/") else settings.LOGIN_URL
            except Exception:
                login_url = getattr(settings, "LOGIN_REDIRECT_URL", "/") or "/"
            if not request.user.is_authenticated and login_url:
                next_url = quote(request.get_full_path())
                login_url = f"{login_url}?next={next_url}" if "?" not in login_url else f"{login_url}&next={next_url}"
            status = 401 if not request.user.is_authenticated else 403
            return JsonResponse(
                {"error": "Unauthorized" if not request.user.is_authenticated else "Forbidden", "login_url": login_url},
                status=status,
            )
        if not request.user.is_authenticated:
            next_url = quote(request.get_full_path())
            return redirect(f"{settings.LOGIN_URL}?next={next_url}")
        return redirect("Forbidden")

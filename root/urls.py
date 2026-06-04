
from django.urls import path, include
from django.views.generic import RedirectView
from root.applist import LOCAL_APPS
from django.conf import settings
from django.conf.urls.static import static

from root import views as root_views

handler400 = root_views.handler400
handler403 = root_views.handler403
handler404 = root_views.handler404
handler500 = root_views.handler500

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboardapp:Dashboard', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),
] + [path(f'{app.replace("app", "")}/', include(f'{app}.urls')) for app in LOCAL_APPS]



urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

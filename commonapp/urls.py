from django.urls import path
from . import views

urlpatterns = [
    path('forbidden/', views.ForbiddenView.as_view(), name='Forbidden'),
    path('filters/apply/', views.GlobalFilterApplyView.as_view(), name='global_filter_apply'),
    path('filters/clear/', views.GlobalFilterClearView.as_view(), name='global_filter_clear'),
]
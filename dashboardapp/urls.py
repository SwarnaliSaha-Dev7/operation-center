from django.urls import path
from . import views

app_name = 'dashboardapp'

urlpatterns = [
    path('', views.ComponentAnalyticsDashboardView.as_view(), name='Dashboard'),
    path('low-stock/', views.DashboardLowStockUpdateView.as_view(), name='dashboard_low_stock'),
]

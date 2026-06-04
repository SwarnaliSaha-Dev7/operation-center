from django.urls import path

from notificationapp import views

app_name = 'notificationapp'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/open/', views.NotificationOpenView.as_view(), name='notification_open'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('api/count/', views.NotificationCountApiView.as_view(), name='notification_count_api'),
]

from django.urls import path

from hardwareissueapp import views

app_name = 'hardwareissueapp'

urlpatterns = [
    path('', views.HardwareIssueListView.as_view(), name='issue_list'),
    path('data/', views.HardwareIssueListDataView.as_view(), name='issue_list_data'),
    path('<int:pk>/', views.HardwareIssueDetailView.as_view(), name='issue_detail'),
    path('<int:pk>/revoke/', views.HardwareIssueRevokeView.as_view(), name='issue_revoke'),
    path('issue/create/', views.HardwareIssueCreateAPIView.as_view(), name='issue_create'),
]

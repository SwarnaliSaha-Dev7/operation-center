from django.urls import path
from . import views

app_name = 'memberapp'

urlpatterns = [
    # Team
    path('team/', views.TeamListView.as_view(), name='team_list'),
    path('team/data/', views.TeamListDataView.as_view(), name='team_list_data'),
    path('team/create/', views.TeamCreateView.as_view(), name='team_create'),
    path('team/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('team/<int:pk>/edit/', views.TeamUpdateView.as_view(), name='team_update'),
    path('team/<int:pk>/copy/', views.TeamCopyView.as_view(), name='team_copy'),
    path('team/<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),
    # Department
    path('department/', views.DepartmentListView.as_view(), name='department_list'),
    path('department/data/', views.DepartmentListDataView.as_view(), name='department_list_data'),
    path('department/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('department/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('department/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('department/<int:pk>/copy/', views.DepartmentCopyView.as_view(), name='department_copy'),
    path('department/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    # Designation
    path('designation/', views.DesignationListView.as_view(), name='designation_list'),
    path('designation/data/', views.DesignationListDataView.as_view(), name='designation_list_data'),
    path('designation/create/', views.DesignationCreateView.as_view(), name='designation_create'),
    path('designation/<int:pk>/', views.DesignationDetailView.as_view(), name='designation_detail'),
    path('designation/<int:pk>/edit/', views.DesignationUpdateView.as_view(), name='designation_update'),
    path('designation/<int:pk>/copy/', views.DesignationCopyView.as_view(), name='designation_copy'),
    path('designation/<int:pk>/delete/', views.DesignationDeleteView.as_view(), name='designation_delete'),
    # Roles (auth Group)
    path('role/', views.RoleListView.as_view(), name='role_list'),
    path('role/data/', views.RoleListDataView.as_view(), name='role_list_data'),
    path('role/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('role/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_update'),
    path('role/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
    # Member
    path('member/profile/', views.ProfileView.as_view(), name='profile'),
    path('member/profile/password/',views.ProfilePasswordChangeView.as_view(),name='profile_password_change'),
    path('member/', views.MemberListView.as_view(), name='member_list'),
    path('member/data/', views.MemberListDataView.as_view(), name='member_list_data'),
    path('member/<int:pk>/active/', views.MemberSetActiveView.as_view(), name='member_set_active'),
    path('member/create/', views.MemberCreateView.as_view(), name='member_create'),
    path('member/<int:pk>/machine-activity/', views.MemberMachineActivityView.as_view(), name='member_machine_activity'),
    path('member/<int:pk>/password/', views.MemberPasswordChangeView.as_view(), name='member_password_change'),
    path('member/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('member/<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_update'),
    path('member/<int:pk>/copy/', views.MemberCopyView.as_view(), name='member_copy'),
    path('member/<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member_delete'),
]

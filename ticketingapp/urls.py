from django.urls import path

from ticketingapp import views

app_name = 'ticketingapp'

urlpatterns = [
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/data/', views.TicketListDataView.as_view(), name='ticket_list_data'),
    path('tickets/create/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:pk>/edit/', views.TicketUpdateView.as_view(), name='ticket_update'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/comment/', views.TicketCommentPostView.as_view(), name='ticket_comment'),
    path('tickets/<int:pk>/action/', views.TicketActionView.as_view(), name='ticket_action'),
]

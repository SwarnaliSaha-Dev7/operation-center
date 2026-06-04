"""
Tests for dashboardapp: Dashboard view and URLs.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


def create_superuser():
    return User.objects.create_superuser(
        username='admin', email='admin@example.com', password='adminpass'
    )


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboardapp:Dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_dashboard_200_when_authenticated(self):
        create_superuser()
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('dashboardapp:Dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_context_has_title(self):
        create_superuser()
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('dashboardapp:Dashboard'))
        self.assertEqual(response.context['title'], 'Dashboard')

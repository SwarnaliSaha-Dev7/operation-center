"""
Tests for commonapp: utils, models, views, mixin, URLs.
"""
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from commonapp.utils import get_current_user, set_current_user, get_datatables_params
from commonapp.models import ActiveManager, CreatedUpdatedByMixin
from commonapp.views import ForbiddenView
from commonapp.mixin import AutoPermissionRequiredMixin

# Use a concrete model that inherits CreatedUpdatedByMixin for manager tests
from memberapp.models import Team

User = get_user_model()


class GetCurrentUserTests(TestCase):
    """Tests for get_current_user and set_current_user."""

    def test_get_current_user_returns_none_when_not_set(self):
        self.assertIsNone(get_current_user())

    def test_set_and_get_current_user(self):
        user = User(username='testuser', email='test@example.com')
        user.save()
        set_current_user(user)
        try:
            self.assertEqual(get_current_user(), user)
        finally:
            set_current_user(None)


class GetDatatablesParamsTests(TestCase):
    """Tests for get_datatables_params."""

    def test_default_params(self):
        factory = RequestFactory()
        request = factory.get('/some-url/')
        params = get_datatables_params(request)
        self.assertEqual(params['draw'], 1)
        self.assertEqual(params['start'], 0)
        self.assertEqual(params['length'], 10)
        self.assertEqual(params['search_value'], '')
        self.assertEqual(params['order_column'], 0)
        self.assertEqual(params['order_dir'], 'asc')

    def test_custom_params_from_get(self):
        factory = RequestFactory()
        request = factory.get(
            '/some-url/',
            {
                'draw': '5',
                'start': '20',
                'length': '25',
                'search[value]': '  query  ',
                'order[0][column]': '2',
                'order[0][dir]': 'desc',
            }
        )
        params = get_datatables_params(request)
        self.assertEqual(params['draw'], 5)
        self.assertEqual(params['start'], 20)
        self.assertEqual(params['length'], 25)
        self.assertEqual(params['search_value'], 'query')
        self.assertEqual(params['order_column'], 2)
        self.assertEqual(params['order_dir'], 'desc')

    def test_length_zero_defaults_to_10(self):
        factory = RequestFactory()
        request = factory.get('/some-url/', {'length': '0'})
        params = get_datatables_params(request)
        self.assertEqual(params['length'], 10)


class ActiveManagerTests(TestCase):
    """Tests for ActiveManager (filter is_delete=False)."""

    def test_queryset_excludes_deleted(self):
        user = User.objects.create_user(username='u1', password='pass')
        Team.objects.create(name='Active Team', code='A', createdby=user, updatedby=user)
        deleted = Team.objects.create(name='Deleted Team', code='D', createdby=user, updatedby=user)
        deleted.is_delete = True
        deleted.save()
        # Team uses objects = ActiveManager()
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(Team.objects.get().name, 'Active Team')


class ForbiddenViewTests(TestCase):
    """Tests for commonapp ForbiddenView."""

    def test_forbidden_view_returns_200(self):
        client = Client()
        response = client.get(reverse('Forbidden'))
        self.assertEqual(response.status_code, 200)

    def test_forbidden_view_context_has_title(self):
        view = ForbiddenView()
        view.request = RequestFactory().get('/forbidden/')
        context = view.get_context_data()
        self.assertEqual(context['title'], 'Forbidden')


class AutoPermissionRequiredMixinTests(TestCase):
    """Tests for AutoPermissionRequiredMixin (superuser bypass, no model)."""

    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            username='super', email='s@x.com', password='pass'
        )

    def test_superuser_passes_test_func_when_no_model(self):
        """When view has no model, test_func returns True."""
        class DummyView(AutoPermissionRequiredMixin):
            pass
        request = self.factory.get('/some-path/')
        request.user = self.superuser
        view = DummyView()
        view.request = request
        self.assertTrue(view.test_func())

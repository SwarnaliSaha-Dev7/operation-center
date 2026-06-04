"""
Tests for hardwareapp: models, forms, views (OS and Processor as representatives).
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from hardwareapp.models import (
    OperatingSystemTable,
    ProcessorTable,
    GraphicsCardTable,
)
from hardwareapp.forms import OperatingSystemForm, ProcessorForm, GraphicsCardForm

User = get_user_model()


def create_superuser():
    return User.objects.create_superuser(
        username='admin', email='admin@example.com', password='adminpass'
    )


# ----- Models -----
class OperatingSystemTableModelTests(TestCase):
    def test_str_returns_name(self):
        obj = OperatingSystemTable(name='Windows', version='11')
        obj.save()
        self.assertEqual(str(obj), 'Windows')


class ProcessorTableModelTests(TestCase):
    def test_str_returns_name(self):
        obj = ProcessorTable(name='Intel i7', cores=8, threads=16)
        obj.save()
        self.assertEqual(str(obj), 'Intel i7')

    def test_defaults(self):
        obj = ProcessorTable.objects.create()
        self.assertEqual(obj.cores, 0)
        self.assertEqual(obj.threads, 0)
        self.assertEqual(obj.quantity, 0)


class GraphicsCardTableModelTests(TestCase):
    def test_str_returns_name(self):
        obj = GraphicsCardTable(name='RTX 3080', memory=10240)
        obj.save()
        self.assertEqual(str(obj), 'RTX 3080')


# ----- Forms -----
class OperatingSystemFormTests(TestCase):
    def test_valid_data(self):
        form = OperatingSystemForm(data={'name': 'Ubuntu', 'version': '22.04'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_name_min_length(self):
        form = OperatingSystemForm(data={'name': 'Ab', 'version': '1'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_version_min_length(self):
        form = OperatingSystemForm(data={'name': 'Linux', 'version': ''})
        self.assertTrue(form.is_valid())  # version can be empty in model
        # Form has clean_version that requires at least 1 char if version provided
        form2 = OperatingSystemForm(data={'name': 'Linux', 'version': 'x'})
        self.assertTrue(form2.is_valid())


class ProcessorFormTests(TestCase):
    def test_valid_data(self):
        form = ProcessorForm(data={
            'name': 'Intel Core i7',
            'brand': 'Intel',
            'model': '12700K',
            'architecture': 'x86_64',
            'cores': 12,
            'threads': 20,
            'frequency': '3.6 GHz',
            'cache': '25MB',
            'quantity': 10,
            'assign': 2,
            'remaining': 8,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_negative_cores_rejected(self):
        form = ProcessorForm(data={
            'name': 'CPU',
            'architecture': 'x86',
            'frequency': '1GHz',
            'cache': '1MB',
            'cores': -1,
            'threads': 0,
            'quantity': 0,
            'assign': 0,
            'remaining': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('cores', form.errors)


class GraphicsCardFormTests(TestCase):
    def test_valid_data(self):
        form = GraphicsCardForm(data={
            'name': 'RTX 3080',
            'brand': 'NVIDIA',
            'model': '3080',
            'memory': 10240,
            'quantity': 5,
            'assign': 0,
            'remaining': 5,
        })
        self.assertTrue(form.is_valid(), form.errors)


# ----- Views (OS and Processor as samples) -----
class OSViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        create_superuser()

    def test_os_list_requires_login(self):
        response = self.client.get(reverse('hardwareapp:os_list'))
        self.assertEqual(response.status_code, 302)

    def test_os_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('hardwareapp:os_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['title'], 'Operating Systems')

    def test_os_create_success(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('hardwareapp:os_create'), {
            'name': 'Windows 11',
            'version': '22H2',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OperatingSystemTable.objects.count(), 1)
        self.assertEqual(OperatingSystemTable.objects.get().name, 'Windows 11')

    def test_os_detail_200(self):
        self.client.login(username='admin', password='adminpass')
        obj = OperatingSystemTable.objects.create(name='Linux', version='6.0')
        response = self.client.get(reverse('hardwareapp:os_detail', kwargs={'pk': obj.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], obj)

    def test_os_list_data_returns_json(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('hardwareapp:os_list_data'), {'draw': '1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('draw', data)
        self.assertIn('recordsTotal', data)
        self.assertIn('data', data)


class ProcessorViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        create_superuser()

    def test_processor_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('hardwareapp:processor_list'))
        self.assertEqual(response.status_code, 200)

    def test_processor_create_success(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('hardwareapp:processor_create'), {
            'name': 'AMD Ryzen 9',
            'brand': 'AMD',
            'model': '5900X',
            'architecture': 'x86_64',
            'cores': 12,
            'threads': 24,
            'frequency': '3.7 GHz',
            'cache': '64MB',
            'quantity': 5,
            'assign': 0,
            'remaining': 5,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProcessorTable.objects.count(), 1)
        self.assertEqual(ProcessorTable.objects.get().name, 'AMD Ryzen 9')

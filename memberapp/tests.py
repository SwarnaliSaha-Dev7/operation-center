"""
Tests for memberapp: models, forms, views (Team, Department, Designation, Member).
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from memberapp.models import Team, Department, Designation
from memberapp.forms import TeamForm, DepartmentForm, DesignationForm, MemberForm, MemberCreateForm

User = get_user_model()


def create_superuser():
    return User.objects.create_superuser(
        username='admin', email='admin@example.com', password='adminpass'
    )


class TeamModelTests(TestCase):
    def test_str_returns_name(self):
        team = Team(name='Engineering', code='ENG')
        team.save()
        self.assertEqual(str(team), 'Engineering')

    def test_ordering_by_name(self):
        Team.objects.create(name='Zebra')
        Team.objects.create(name='Alpha')
        names = [t.name for t in Team.objects.filter(is_delete=False)]
        self.assertEqual(names, ['Alpha', 'Zebra'])


class DepartmentModelTests(TestCase):
    def test_str_returns_name(self):
        dept = Department(name='HR', code='HR')
        dept.save()
        self.assertEqual(str(dept), 'HR')


class DesignationModelTests(TestCase):
    def test_str_returns_name(self):
        des = Designation(name='Developer', code='DEV')
        des.save()
        self.assertEqual(str(des), 'Developer')


class UserModelTests(TestCase):
    def test_str_returns_full_name_or_username(self):
        user = User(username='jdoe', first_name='John', last_name='Doe')
        user.save()
        self.assertEqual(str(user), 'John Doe')
        user2 = User(username='nofull')
        user2.save()
        self.assertEqual(str(user2), 'nofull')


class TeamFormTests(TestCase):
    def test_valid_data(self):
        form = TeamForm(data={'name': 'Dev Team', 'code': 'DEV', 'description': ''})
        self.assertTrue(form.is_valid(), form.errors)

    def test_name_min_length(self):
        form = TeamForm(data={'name': 'A', 'code': '', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_name_stripped(self):
        form = TeamForm(data={'name': '  Ok  ', 'code': '', 'description': ''})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Ok')


class DepartmentFormTests(TestCase):
    def test_valid_data(self):
        form = DepartmentForm(data={'name': 'Engineering', 'code': 'ENG', 'description': ''})
        self.assertTrue(form.is_valid(), form.errors)

    def test_name_min_length(self):
        form = DepartmentForm(data={'name': 'A', 'code': '', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class DesignationFormTests(TestCase):
    def test_valid_data(self):
        form = DesignationForm(data={'name': 'Senior Dev', 'code': 'SR', 'description': ''})
        self.assertTrue(form.is_valid(), form.errors)


class MemberCreateFormTests(TestCase):
    def test_valid_data(self):
        form = MemberCreateForm(data={
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'email': '',
            'employee_id': '',
            'phone': '',
            'team': '',
            'department': '',
            'designation': '',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_weak_password_accepted(self):
        """Member create skips global AUTH_PASSWORD_VALIDATORS strength rules."""
        form = MemberCreateForm(data={
            'username': 'weakpwuser',
            'password1': '123',
            'password2': '123',
            'first_name': 'W',
            'last_name': 'U',
            'email': '',
            'employee_id': '',
            'phone': '',
            'team': '',
            'department': '',
            'designation': '',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_employee_id(self):
        User.objects.create_user(username='existing', password='p', employee_id='E001')
        form = MemberCreateForm(data={
            'username': 'newuser2',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'employee_id': 'E001',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('employee_id', form.errors)

    def test_invalid_phone_rejected(self):
        form = MemberCreateForm(data={
            'username': 'u1',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'phone': 'invalid@@',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)


class MemberFormTests(TestCase):
    def test_employee_id_unique_excludes_self(self):
        user = User.objects.create_user(username='u1', password='p', employee_id='E001')
        form = MemberForm(instance=user, data={
            'username': 'u1',
            'first_name': '',
            'last_name': '',
            'email': '',
            'employee_id': 'E001',
            'phone': '',
            'team': '',
            'department': '',
            'designation': '',
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)


class TeamViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = create_superuser()

    def test_team_list_requires_login(self):
        response = self.client.get(reverse('memberapp:team_list'))
        self.assertEqual(response.status_code, 302)

    def test_team_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('memberapp:team_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context)
        self.assertEqual(response.context['title'], 'Teams')

    def test_team_create_redirects_after_post(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('memberapp:team_create'), {
            'name': 'New Team',
            'code': 'NT',
            'description': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(Team.objects.get().name, 'New Team')

    def test_team_detail_200(self):
        self.client.login(username='admin', password='adminpass')
        team = Team.objects.create(name='T1', code='T1')
        response = self.client.get(reverse('memberapp:team_detail', kwargs={'pk': team.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], team)

    def test_team_list_data_returns_json(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('memberapp:team_list_data'), {'draw': '1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('draw', data)
        self.assertIn('recordsTotal', data)
        self.assertIn('data', data)


class DepartmentViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        create_superuser()

    def test_department_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('memberapp:department_list'))
        self.assertEqual(response.status_code, 200)

    def test_department_create_success(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('memberapp:department_create'), {
            'name': 'Engineering',
            'code': 'ENG',
            'description': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Department.objects.count(), 1)


class DesignationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        create_superuser()

    def test_designation_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('memberapp:designation_list'))
        self.assertEqual(response.status_code, 200)


class MemberViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        create_superuser()

    def test_member_list_200_for_superuser(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('memberapp:member_list'))
        self.assertEqual(response.status_code, 200)

    def test_member_create_success(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('memberapp:member_create'), {
            'username': 'member1',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Member',
            'last_name': 'One',
            'email': '',
            'employee_id': '',
            'phone': '',
            'team': '',
            'department': '',
            'designation': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='member1').exists())

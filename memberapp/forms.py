import re
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from memberapp.models import Team, Department, Designation

User = get_user_model()
INPUT_CLASS = 'w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
# Django auth Group (shown as "Roles") — checkbox list instead of multi-select
ROLE_GROUPS_CHECKBOX_WIDGET = forms.CheckboxSelectMultiple(
    attrs={
        'class': (
            'rounded border-slate-300 text-amber-600 focus:ring-amber-500 '
            'h-4 w-4 shrink-0'
        ),
    },
)


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'code', 'description']
        labels = {'name': 'Name', 'code': 'Code', 'description': 'Description'}
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }
        help_texts = {
            'name': 'Enter the team name (e.g. Development, QA).',
            'code': 'Optional short code or abbreviation for the team.',
            'description': 'Optional description of the team and its responsibilities.',
        }
        error_messages = {
            'name': {
                'required': 'Team name is required.',
                'max_length': 'Team name must be 255 characters or fewer.',
            },
            'code': {'max_length': 'Code must be 64 characters or fewer.'},
            'description': {'max_length': 'Description is too long.'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Team name must be at least 2 characters.')
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.strip()
            if len(code) > 64:
                raise forms.ValidationError('Code must be 64 characters or fewer.')
        return code or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['name', 'code']:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', name.capitalize())


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        labels = {'name': 'Name', 'code': 'Code', 'description': 'Description'}
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }
        help_texts = {
            'name': 'Enter the department name (e.g. Engineering, HR).',
            'code': 'Optional short code or abbreviation for the department.',
            'description': 'Optional description of the department.',
        }
        error_messages = {
            'name': {
                'required': 'Department name is required.',
                'max_length': 'Department name must be 255 characters or fewer.',
            },
            'code': {'max_length': 'Code must be 64 characters or fewer.'},
            'description': {'max_length': 'Description is too long.'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Department name must be at least 2 characters.')
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.strip()
            if len(code) > 64:
                raise forms.ValidationError('Code must be 64 characters or fewer.')
        return code or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['name', 'code']:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', name.capitalize())


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'code', 'description']
        labels = {'name': 'Name', 'code': 'Code', 'description': 'Description'}
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }
        help_texts = {
            'name': 'Enter the designation or job title (e.g. Senior Developer, Manager).',
            'code': 'Optional short code or abbreviation for the designation.',
            'description': 'Optional description of the role and responsibilities.',
        }
        error_messages = {
            'name': {
                'required': 'Designation name is required.',
                'max_length': 'Designation name must be 255 characters or fewer.',
            },
            'code': {'max_length': 'Code must be 64 characters or fewer.'},
            'description': {'max_length': 'Description is too long.'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Designation name must be at least 2 characters.')
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.strip()
            if len(code) > 64:
                raise forms.ValidationError('Code must be 64 characters or fewer.')
        return code or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['name', 'code']:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', name.capitalize())


class RoleForm(forms.ModelForm):
    """Django auth Group shown in the UI as a member role."""

    class Meta:
        model = Group
        fields = ['name']
        labels = {'name': 'Role name'}
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': INPUT_CLASS,
                    'placeholder': 'e.g. IT support, Inventory clerk',
                }
            ),
        }
        help_texts = {
            'name': 'Unique name. Members assigned this role receive all permissions you set below.',
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Role name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Role name must be at least 2 characters.')
        qs = Group.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A role with this name already exists.')
        return name


class ProfilePasswordChangeForm(PasswordChangeForm):
    """Styled fields for the self-service password change page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault('class', INPUT_CLASS)


class ProfileForm(forms.ModelForm):
    """Self-service profile: name, email, and phone only (no roles or org structure here)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
            'phone': 'Phone',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }
        help_texts = {
            'phone': 'Optional contact number. Digits, spaces, +, -, () are allowed.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not phone:
                return None
            if len(phone) > 32:
                raise forms.ValidationError('Phone number must be 32 characters or fewer.')
            if not re.match(r'^[\d\s+\-().]+$', phone):
                raise forms.ValidationError(
                    'Enter a valid phone number (digits, spaces, +, -, (), . allowed).'
                )
        return phone or None


class MemberSetPasswordForm(SetPasswordForm):
    """Admin-set password: no Django strength rules; confirmation must match only."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('new_password1', 'new_password2'):
            if name in self.fields:
                self.fields[name].help_text = ''

    def validate_password_for_user(self, user, password_field_name='new_password2'):
        password = self.cleaned_data.get(password_field_name)
        if password:
            try:
                password_validation.validate_password(password, user, password_validators=[])
            except ValidationError as error:
                self.add_error(password_field_name, error)


class MemberCreateForm(UserCreationForm):
    """Form for creating a new member (User with member fields)."""
    class Meta:
        model = User
        fields = [
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'email',
            'employee_id',
            'phone',
            'email_password',
            'discord_id',
            'discord_password',
            'team',
            'department',
            'designation',
            'groups',
        ]

        labels = {
            'username': 'Username',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
            'employee_id': 'Employee ID',
            'email_password':'Email Password',
            'discord_id':'Discord Id',
            'discord_password':'Discord Password',
            'phone': 'Phone',
            'team': 'Team',
            'department': 'Department',
            'designation': 'Designation',
            'groups': 'Roles',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'email_password': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'discord_id': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'discord_password': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'employee_id': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'department': forms.Select(attrs={'class': INPUT_CLASS}),
            'designation': forms.Select(attrs={'class': INPUT_CLASS}),
            'groups': ROLE_GROUPS_CHECKBOX_WIDGET,
        }
        help_texts = {
            'username': 'Required. Letters, digits and @/./+/-/_ only.',
            'employee_id': 'Optional unique employee or staff ID (e.g. EMP001).',
            'phone': 'Optional contact number. Digits, spaces, +, -, () are allowed.',
            'team': 'Optional team this member belongs to.',
            'department': 'Optional department this member belongs to.',
            'designation': 'Optional job title or designation.',
            'groups': 'Check one or more roles. Permissions come from roles plus any direct assignments below.',
        }
        error_messages = {
            'username': {'required': 'Username is required.'},
            'employee_id': {'max_length': 'Employee ID must be 64 characters or fewer.'},
            'phone': {'max_length': 'Phone number must be 32 characters or fewer.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['username', 'password1', 'password2']:
            if f in self.fields:
                self.fields[f].widget.attrs.setdefault('class', INPUT_CLASS)
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['team'].queryset = Team.objects.filter(is_delete=False).order_by('name')
        self.fields['department'].queryset = Department.objects.filter(is_delete=False).order_by('name')
        self.fields['designation'].queryset = Designation.objects.filter(is_delete=False).order_by('name')
        self.fields['team'].required = False
        self.fields['department'].required = False
        self.fields['designation'].required = False
        self.fields['email'].required = False
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        self.fields['groups'].required = False

    def validate_password_for_user(self, user, password_field_name='password2'):
        password = self.cleaned_data.get(password_field_name)
        if password:
            try:
                password_validation.validate_password(password, user, password_validators=[])
            except ValidationError as error:
                self.add_error(password_field_name, error)

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            employee_id = employee_id.strip()
            if not employee_id:
                return None
            if User.objects.filter(employee_id__iexact=employee_id).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError('A user with this employee ID already exists.')
        return employee_id or None

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not phone:
                return None
            if len(phone) > 32:
                raise forms.ValidationError('Phone number must be 32 characters or fewer.')
            if not re.match(r'^[\d\s+\-().]+$', phone):
                raise forms.ValidationError('Enter a valid phone number (digits, spaces, +, -, (), . allowed).')
        return phone or None


class MemberForm(forms.ModelForm):
    """Form for editing a member (User with member fields). No password; username read-only."""
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'email_password',
            'discord_id',
            'discord_password',
            'employee_id',
            'phone',
            'team',
            'department',
            'designation',
            'groups',
            'is_active',
        ]
        labels = {
            'username': 'Username',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
            'employee_id': 'Employee ID',
            'phone': 'Phone',
            'team': 'Team',
            'email_password' :'Email Password',
            'discord_id' : 'Discord id',
            'discord_password' : 'Discord Password',
            'department': 'Department',
            'designation': 'Designation',
            'groups': 'Roles',
            'is_active': 'Active',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'email_password': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'discord_id': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'discord_password': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'employee_id': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'team': forms.Select(attrs={'class': INPUT_CLASS}),
            'department': forms.Select(attrs={'class': INPUT_CLASS}),
            'designation': forms.Select(attrs={'class': INPUT_CLASS}),
            'groups': ROLE_GROUPS_CHECKBOX_WIDGET,
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-slate-300'}),
        }
        help_texts = {
            'employee_id': 'Optional unique employee or staff ID (e.g. EMP001).',
            'phone': 'Optional contact number. Digits, spaces, +, -, () are allowed.',
            'team': 'Optional team this member belongs to.',
            'department': 'Optional department this member belongs to.',
            'designation': 'Optional job title or designation.',
            'groups': 'Check one or more roles to assign permission bundles. Direct checkboxes in the matrix below add permissions only for this member.',
        }
        error_messages = {
            'employee_id': {'max_length': 'Employee ID must be 64 characters or fewer.'},
            'phone': {'max_length': 'Phone number must be 32 characters or fewer.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].disabled = True
        self.fields['team'].queryset = Team.objects.filter(is_delete=False).order_by('name')
        self.fields['department'].queryset = Department.objects.filter(is_delete=False).order_by('name')
        self.fields['designation'].queryset = Designation.objects.filter(is_delete=False).order_by('name')
        self.fields['team'].required = False
        self.fields['department'].required = False
        self.fields['designation'].required = False
        self.fields['email'].required = False
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        self.fields['groups'].required = False

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            employee_id = employee_id.strip()
            if not employee_id:
                return None
            if User.objects.filter(employee_id__iexact=employee_id).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('A user with this employee ID already exists.')
        return employee_id or None

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            if not phone:
                return None
            if len(phone) > 32:
                raise forms.ValidationError('Phone number must be 32 characters or fewer.')
            if not re.match(r'^[\d\s+\-().]+$', phone):
                raise forms.ValidationError('Enter a valid phone number (digits, spaces, +, -, (), . allowed).')
        return phone or None

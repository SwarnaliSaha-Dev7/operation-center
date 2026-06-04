from django.contrib import messages
import json

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)

from commonapp.mixin import AutoPermissionRequiredMixin
from commonapp.permission_matrix import (
    filter_valid_permission_ids,
    permission_matrix_rows,
    permission_matrix_rows_with_applied,
    permission_matrix_rows_with_applied_for_group,
)
from commonapp.global_filters import (
    apply_department_list_global_filters,
    apply_designation_list_global_filters,
    apply_role_list_global_filters,
    apply_team_list_global_filters,
    apply_user_list_filters,
)
from commonapp.utils import get_datatables_params
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordChangeView
from hardwareapp.machine_history import member_machine_activity_data
from memberapp.models import Team, Department, Designation
from memberapp.session_online import logged_in_user_ids
from memberapp.forms import (
    TeamForm,
    DepartmentForm,
    DesignationForm,
    MemberForm,
    MemberCreateForm,
    MemberSetPasswordForm,
    ProfileForm,
    ProfilePasswordChangeForm,
    RoleForm,
)

User = get_user_model()


def _member_queryset_for_viewer(viewer):
    """
    Users visible in member list / detail / edit for the current viewer.
    Superusers see everyone. Others never see superusers; non-staff never see staff.
    """
    qs = User.objects.all()
    if viewer.is_superuser:
        return qs
    qs = qs.filter(is_superuser=False)
    if not viewer.is_staff:
        qs = qs.filter(is_staff=False)
    return qs


# ---------- Team ----------
class TeamListView(AutoPermissionRequiredMixin, ListView):
    model = Team
    template_name = 'memberapp/team/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Teams'
        context['table_columns'] = ['Sl', 'Name', 'Code', 'Actions']
        return context


class TeamListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = Team.objects.filter(is_delete=False)
        qs = apply_team_list_global_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(
                Q(name__icontains=params['search_value'])
                | Q(code__icontains=params['search_value'])
            )
        records_filtered = qs.count()
        order_cols = ['id', 'name', 'code']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('memberapp.view_team')
        can_edit = request.user.has_perm('memberapp.change_team')
        can_copy = request.user.has_perm('memberapp.add_team')
        can_delete = request.user.has_perm('memberapp.delete_team')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {'url_name': 'memberapp:team_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view},
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'memberapp:team_detail',
                    'update_url_name': 'memberapp:team_update',
                    'copy_url_name': 'memberapp:team_copy',
                    'delete_url_name': 'memberapp:team_delete',
                    'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete,
                },
                request=request,
            )
            data.append([counter, name_cell, obj.code or '—', actions_cell])
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class TeamDetailView(AutoPermissionRequiredMixin, DetailView):
    model = Team
    template_name = 'memberapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        context['fields'] = [
            {"label": "Name", "value": obj.name},
            {"label": "Code", "value": obj.code},
            {"label": "Description", "value": obj.description or "—"},
        ]
        context['update_url'] = reverse('memberapp:team_update', args=[obj.pk])
        context['delete_url'] = reverse('memberapp:team_delete', args=[obj.pk])
        context['list_url'] = reverse('memberapp:team_list')
        context['can_edit'] = self.request.user.has_perm('memberapp.change_team')
        context['can_delete'] = self.request.user.has_perm('memberapp.delete_team')
        return context


class TeamCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'memberapp/team/form.html'
    success_url = reverse_lazy('memberapp:team_list')
    success_message = 'Team created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Team'
        return context


class TeamUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'memberapp/team/form.html'
    success_url = reverse_lazy('memberapp:team_list')
    context_object_name = 'object'
    success_message = 'Team updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Team'
        return context


class TeamDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = Team
    template_name = 'memberapp/team/confirm_delete.html'
    success_url = reverse_lazy('memberapp:team_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Team'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Team deleted.')
        return super().delete(request, *args, **kwargs)


class TeamCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(Team, pk=pk)
        copy = Team(name=f'{obj.name} (Copy)', code=obj.code, description=obj.description)
        copy.save()
        messages.success(request, 'Team copied.')
        return redirect('memberapp:team_list')


# ---------- Department ----------
class DepartmentListView(AutoPermissionRequiredMixin, ListView):
    model = Department
    template_name = 'memberapp/department/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Departments'
        context['table_columns'] = ['Sl', 'Name', 'Code', 'Actions']
        return context


class DepartmentListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = Department.objects.filter(is_delete=False)
        qs = apply_department_list_global_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(
                Q(name__icontains=params['search_value'])
                | Q(code__icontains=params['search_value'])
            )
        records_filtered = qs.count()
        order_cols = ['id', 'name', 'code']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('memberapp.view_department')
        can_edit = request.user.has_perm('memberapp.change_department')
        can_copy = request.user.has_perm('memberapp.add_department')
        can_delete = request.user.has_perm('memberapp.delete_department')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {'url_name': 'memberapp:department_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view},
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'memberapp:department_detail',
                    'update_url_name': 'memberapp:department_update',
                    'copy_url_name': 'memberapp:department_copy',
                    'delete_url_name': 'memberapp:department_delete',
                    'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete,
                },
                request=request,
            )
            data.append([counter, name_cell, obj.code or '—', actions_cell])
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class DepartmentDetailView(AutoPermissionRequiredMixin, DetailView):
    model = Department
    template_name = 'memberapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        context['fields'] = [
            {"label": "Name", "value": obj.name},
            {"label": "Code", "value": obj.code},
            {"label": "Description", "value": obj.description or "—"},
        ]
        context['update_url'] = reverse('memberapp:department_update', args=[obj.pk])
        context['delete_url'] = reverse('memberapp:department_delete', args=[obj.pk])
        context['list_url'] = reverse('memberapp:department_list')
        context['can_edit'] = self.request.user.has_perm('memberapp.change_department')
        context['can_delete'] = self.request.user.has_perm('memberapp.delete_department')
        return context


class DepartmentCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'memberapp/department/form.html'
    success_url = reverse_lazy('memberapp:department_list')
    success_message = 'Department created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Department'
        return context


class DepartmentUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'memberapp/department/form.html'
    success_url = reverse_lazy('memberapp:department_list')
    context_object_name = 'object'
    success_message = 'Department updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Department'
        return context


class DepartmentDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = Department
    template_name = 'memberapp/department/confirm_delete.html'
    success_url = reverse_lazy('memberapp:department_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Department'
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Department deleted.')
        return super().delete(request, *args, **kwargs)


class DepartmentCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(Department, pk=pk)
        copy = Department(name=f'{obj.name} (Copy)', code=obj.code, description=obj.description)
        copy.save()
        messages.success(request, 'Department copied.')
        return redirect('memberapp:department_list')


# ---------- Designation ----------
class DesignationListView(AutoPermissionRequiredMixin, ListView):
    model = Designation
    template_name = 'memberapp/designation/list.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Designations'
        context['table_columns'] = ['Sl', 'Name', 'Code', 'Actions']
        return context


class DesignationListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = Designation.objects.filter(is_delete=False)
        qs = apply_designation_list_global_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(
                Q(name__icontains=params['search_value'])
                | Q(code__icontains=params['search_value'])
            )
        records_filtered = qs.count()
        order_cols = ['id', 'name', 'code']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('id')
        page = qs[params['start']:params['start'] + params['length']]
        can_view = request.user.has_perm('memberapp.view_designation')
        can_edit = request.user.has_perm('memberapp.change_designation')
        can_copy = request.user.has_perm('memberapp.add_designation')
        can_delete = request.user.has_perm('memberapp.delete_designation')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {'url_name': 'memberapp:designation_detail', 'pk': obj.pk, 'label': obj.name, 'can_view': can_view},
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'memberapp:designation_detail',
                    'update_url_name': 'memberapp:designation_update',
                    'copy_url_name': 'memberapp:designation_copy',
                    'delete_url_name': 'memberapp:designation_delete',
                    'obj': obj, 'can_view': can_view, 'can_edit': can_edit, 'can_copy': can_copy, 'can_delete': can_delete,
                },
                request=request,
            )
            data.append([counter, name_cell, obj.code or '—', actions_cell])
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class DesignationDetailView(AutoPermissionRequiredMixin, DetailView):
    model = Designation
    template_name = 'memberapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = obj.name
        context['fields'] = [
            {"label": "Name", "value": obj.name},
            {"label": "Code", "value": obj.code},
            {"label": "Description", "value": obj.description or "—"},
        ]
        context['update_url'] = reverse('memberapp:designation_update', args=[obj.pk])
        context['delete_url'] = reverse('memberapp:designation_delete', args=[obj.pk])
        context['list_url'] = reverse('memberapp:designation_list')
        context['can_edit'] = self.request.user.has_perm('memberapp.change_designation')
        context['can_delete'] = self.request.user.has_perm('memberapp.delete_designation')
        return context


class DesignationCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'memberapp/designation/form.html'
    success_url = reverse_lazy('memberapp:designation_list')
    success_message = 'Designation created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Designation'
        return context


class DesignationUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'memberapp/designation/form.html'
    success_url = reverse_lazy('memberapp:designation_list')
    context_object_name = 'object'
    success_message = 'Designation updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Designation'
        return context


class DesignationDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = Designation
    template_name = 'memberapp/common-html/delete.html'
    success_url = reverse_lazy('memberapp:designation_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Employee'

        context['object_display'] = (
            f"{obj.name}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'memberapp.delete_designation'
        )

        #  cancel button
        context['cancel_url'] = reverse('memberapp:designation_list')
        return context


class DesignationCopyView(AutoPermissionRequiredMixin, View):
    def get(self, request, pk):
        obj = get_object_or_404(Designation, pk=pk)
        copy = Designation(name=f'{obj.name} (Copy)', code=obj.code, description=obj.description)
        copy.save()
        messages.success(request, 'Designation copied.')
        return redirect('memberapp:designation_list')


# ---------- Roles (Django auth Group + permission matrix) ----------
class RoleListView(AutoPermissionRequiredMixin, ListView):
    model = Group
    template_name = 'memberapp/role/list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return Group.objects.annotate(_member_count=Count('user', distinct=True)).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Roles'
        context['table_columns'] = ['Sl', 'Role name', 'Members', 'Actions']
        return context


class RoleListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = Group.objects.annotate(_member_count=Count('user', distinct=True))
        qs = apply_role_list_global_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            sv = params['search_value']
            qs = qs.filter(name__icontains=sv)
        records_filtered = qs.count()
        order_cols = ['id', 'name', '_member_count']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('name')
        page = qs[params['start'] : params['start'] + params['length']]
        can_edit = request.user.has_perm('auth.change_group')
        can_delete = request.user.has_perm('auth.delete_group')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'memberapp:role_update',
                    'update_url_name': 'memberapp:role_update',
                    'copy_url_name': 'memberapp:role_update',
                    'delete_url_name': 'memberapp:role_delete',
                    'obj': obj,
                    'can_view': False,
                    'can_edit': can_edit,
                    'can_copy': False,
                    'can_delete': can_delete,
                },
                request=request,
            )
            data.append([counter, obj.name, obj._member_count, actions_cell])
        return JsonResponse(
            {
                'draw': params['draw'],
                'recordsTotal': records_total,
                'recordsFiltered': records_filtered,
                'data': data,
            }
        )


class RoleCreateView(AutoPermissionRequiredMixin, CreateView):
    model = Group
    form_class = RoleForm
    template_name = 'memberapp/role/form.html'
    success_url = reverse_lazy('memberapp:role_list')
    success_message = 'Role created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add role'
        context['show_role_permissions'] = True
        context['permission_matrix_rows'] = permission_matrix_rows()
        context['applied_permission_ids'] = set()
        context['permission_matrix_readonly'] = False
        context['permission_matrix_help'] = 'role'
        return context

    def form_valid(self, form):
        self.object = form.save()
        self.object.permissions.set(
            filter_valid_permission_ids(self.request.POST.getlist('user_perms'))
        )
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


class RoleUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    form_class = RoleForm
    template_name = 'memberapp/role/form.html'
    success_url = reverse_lazy('memberapp:role_list')
    success_message = 'Role updated.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit role — {self.object.name}'
        rows, applied_ids = permission_matrix_rows_with_applied_for_group(self.object)
        context['show_role_permissions'] = True
        context['permission_matrix_rows'] = rows
        context['applied_permission_ids'] = applied_ids
        context['permission_matrix_readonly'] = False
        context['permission_matrix_help'] = 'role'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.permissions.set(
            filter_valid_permission_ids(self.request.POST.getlist('user_perms'))
        )
        return response


class RoleDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'memberapp/common-html/delete.html'
    success_url = reverse_lazy('memberapp:role_list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete role'
        context['object_display'] = self.object.name
        context['can_delete'] = self.request.user.has_perm('auth.delete_group')
        context['cancel_url'] = reverse('memberapp:role_list')
        return context


# ---------- Member (custom User with member fields) ----------
class ProfilePasswordChangeView(PasswordChangeView):
    """Current user changes their own password (styled form, return to profile)."""

    form_class = ProfilePasswordChangeForm
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('memberapp:profile')


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Current user updates their own contact details."""

    model = User
    form_class = ProfileForm
    template_name = 'memberapp/member/profile.html'
    success_url = reverse_lazy('memberapp:profile')
    success_message = 'Your profile was updated.'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        u = self.request.user
        context['title'] = 'My profile'
        context['role_names'] = ', '.join(sorted(g.name for g in u.groups.all())) or '—'
        context['machine_activity_url'] = reverse(
            'memberapp:member_machine_activity', args=[u.pk]
        )
        return context


class MemberListView(AutoPermissionRequiredMixin, ListView):
    model = User
    template_name = 'memberapp/member/list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return _member_queryset_for_viewer(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Members'
        context['table_heading'] = 'Members'
        context['table_columns'] = [
            'Sl',
            'Username',
            'Employee ID',
            'Active',
            'Online',
            'Roles',
            'Team',
            'Department',
            'Designation',
            'Actions',
        ]
        return context


class MemberSetActiveView(LoginRequiredMixin, View):
    """Toggle member is_active from the list (JSON POST). Requires change on member User."""

    http_method_names = ['post']

    def post(self, request, pk, *args, **kwargs):
        if not request.user.has_perm('memberapp.change_user'):
            return JsonResponse(
                {'ok': False, 'error': 'You do not have permission to change members.'},
                status=403,
            )
        member = get_object_or_404(_member_queryset_for_viewer(request.user), pk=pk)
        if member.pk == request.user.pk:
            return JsonResponse(
                {'ok': False, 'error': 'You cannot change your own active status from the list.'},
                status=400,
            )
        ct = (request.content_type or '').split(';')[0].strip().lower()
        if ct == 'application/json':
            try:
                body = json.loads(request.body.decode() or '{}')
            except (json.JSONDecodeError, UnicodeDecodeError):
                body = {}
            is_active = bool(body.get('is_active'))
        else:
            raw = request.POST.get('is_active')
            is_active = str(raw).lower() in ('true', '1', 'on', 'yes')
        member.is_active = is_active
        member.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': member.is_active})


class MemberListDataView(AutoPermissionRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = (
            _member_queryset_for_viewer(request.user)
            .select_related('team', 'department', 'designation')
            .prefetch_related('groups')
        )
        qs = apply_user_list_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            qs = qs.filter(
                Q(username__icontains=params['search_value'])
                | Q(first_name__icontains=params['search_value'])
                | Q(last_name__icontains=params['search_value'])
                | Q(email__icontains=params['search_value'])
                | Q(employee_id__icontains=params['search_value'])
                | Q(phone__icontains=params['search_value'])
                | Q(team__name__icontains=params['search_value'])
                | Q(department__name__icontains=params['search_value'])
                | Q(designation__name__icontains=params['search_value'])
                | Q(groups__name__icontains=params['search_value'])
                | Q(email_password__icontains=params['search_value'])
                | Q(discord_id__icontains=params['search_value'])
                | Q(discord_password__icontains=params['search_value'])

            ).distinct()
        records_filtered = qs.count()
        order_cols = [
            'id',
            'username',
            'employee_id',
            'is_active',
            'username',
            'username',
            'team__name',
            'department__name',
            'designation__name',
        ]
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('username')
        page = qs[params['start']:params['start'] + params['length']]
        online_ids = logged_in_user_ids()
        can_view = request.user.has_perm('memberapp.view_user')
        can_edit = request.user.has_perm('memberapp.change_user')
        can_copy = request.user.has_perm('memberapp.add_user')
        can_delete = request.user.has_perm('memberapp.delete_user')
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'memberapp:member_detail',
                    'update_url_name': 'memberapp:member_update',
                    'copy_url_name': 'memberapp:member_copy',
                    'delete_url_name': 'memberapp:member_delete',
                    'password_url_name': 'memberapp:member_password_change',
                    'member_activity_url_name': 'memberapp:member_machine_activity',
                    'obj': obj,
                    'can_view': can_view,
                    'can_view_member_activity': can_view,
                    'can_edit': can_edit,
                    'can_change_password': can_edit,
                    'can_copy': can_copy,
                    'can_delete': can_delete,
                },
                request=request,
            )
            roles_display = ', '.join(sorted(g.name for g in obj.groups.all())) or '—'
            can_toggle_active = can_edit and obj.pk != request.user.pk
            active_html = render_to_string(
                'memberapp/member/_list_active_cell.html',
                {
                    'pk': obj.pk,
                    'is_active': obj.is_active,
                    'can_toggle': can_toggle_active,
                },
                request=request,
            )
            if obj.pk in online_ids:
                online_html = mark_safe(
                    '<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-sky-100 text-sky-800">'
                    '<span class="inline-block h-1.5 w-1.5 rounded-full bg-sky-500 shrink-0" aria-hidden="true"></span>Online</span>'
                )
            else:
                online_html = mark_safe(
                    '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500">Offline</span>'
                )
            data.append([
                counter,
                obj.username or '—',
                obj.employee_id or '—',
                active_html,
                online_html,
                roles_display,
                obj.team.name if obj.team else '—',
                obj.department.name if obj.department else '—',
                obj.designation.name if obj.designation else '—',
                actions_cell,
            ])
        return JsonResponse({
            'draw': params['draw'],
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        })


class MemberDetailView(AutoPermissionRequiredMixin, DetailView):
    model = User
    template_name = 'memberapp/common-html/details.html'
    context_object_name = 'object'

    def get_queryset(self):
        return _member_queryset_for_viewer(self.request.user).prefetch_related('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = self.object.get_full_name() or self.object.username
        role_names = ', '.join(sorted(g.name for g in obj.groups.all())) or '—'

        context['fields'] = [
            {"label": "username", "value": obj.username},
            {"label": "Employee_id", "value": obj.employee_id},
            {"label": "Roles", "value": role_names},
            {"label": "Phone", "value": obj.phone},
            {"label": "Team", "value": obj.team},
            {"label": "email", "value": obj.email},
            {"label": "email_password", "value": obj.email_password},
            {"label": "discord_id", "value": obj.discord_id},
            {"label": "discord_password", "value": obj.discord_password},
            {"label": "department", "value": obj.department},
            {"label": "designation", "value": obj.designation},
        ]
#  Buttons (same pattern you used before)
        context['update_url'] = reverse('memberapp:member_update', args=[obj.pk])
        context['copy_url'] = reverse('memberapp:member_copy', args=[obj.pk])
        context['delete_url'] = reverse('memberapp:member_delete', args=[obj.pk])
        context['list_url'] = reverse('memberapp:member_list')
        context['can_edit'] = self.request.user.has_perm('memberapp.change_user')
        context['can_copy'] = self.request.user.has_perm('memberapp.add_user')
        context['can_delete'] = self.request.user.has_perm('memberapp.delete_user')
        rows, applied_ids = permission_matrix_rows_with_applied(self.object, effective=True)
        context['show_member_permissions'] = True
        context['permission_matrix_rows'] = rows
        context['applied_permission_ids'] = applied_ids
        context['permission_matrix_readonly'] = True
        context['permission_matrix_help'] = 'view'
        context['machine_activity_url'] = reverse('memberapp:member_machine_activity', args=[obj.pk])
        context['can_view_machine_activity'] = True

        return context


class MemberMachineActivityView(AutoPermissionRequiredMixin, DetailView):
    """Per-member timeline: machine assignments, hardware upgrades/downgrades, OS (as assignee)."""

    model = User
    template_name = 'memberapp/member/machine_activity.html'
    context_object_name = 'member_user'

    def test_func(self):
        user = self.request.user
        if user.is_authenticated and str(user.pk) == str(self.kwargs.get('pk')):
            return True
        return super().test_func()

    def get_queryset(self):
        return _member_queryset_for_viewer(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = member_machine_activity_data(self.object)
        context.update(payload)
        context['title'] = (
            f'Machine activity — {self.object.get_full_name() or self.object.username}'
        )
        context['detail_url'] = reverse('memberapp:member_detail', args=[self.object.pk])
        context['list_url'] = reverse('memberapp:member_list')
        context['update_url'] = reverse('memberapp:member_update', args=[self.object.pk])
        context['can_edit'] = self.request.user.has_perm('memberapp.change_user')
        return context


class MemberCreateView(AutoPermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = MemberCreateForm
    template_name = 'memberapp/member/form.html'
    success_url = reverse_lazy('memberapp:member_list')
    success_message = 'Member created.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Member'
        context['show_member_permissions'] = True
        context['permission_matrix_rows'] = permission_matrix_rows()
        context['applied_permission_ids'] = set()
        context['permission_matrix_help'] = 'create'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        selected = filter_valid_permission_ids(self.request.POST.getlist('user_perms'))
        self.object.user_permissions.set(selected)
        return response

    def get_initial(self):
        initial = super().get_initial()
        q = self.request.GET
        try:
            if q.get('discord_id'):
              initial['discord_id'] = q.get('discord_id')

            if q.get('email_password'):
              initial['email_password'] = q.get('email_password')

            if q.get('discord_password'):
              initial['discord_password'] = q.get('discord_password')

            if q.get('team'):
                initial['team'] = int(q.get('team'))
            if q.get('department'):
                initial['department'] = int(q.get('department'))
            if q.get('designation'):
                initial['designation'] = int(q.get('designation'))
        except (TypeError, ValueError):
            pass
        if q.get('phone'):
            initial['phone'] = q.get('phone')
        if q.get('employee_id'):
            initial['employee_id'] = q.get('employee_id')
        return initial


class MemberUpdateView(AutoPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = MemberForm
    template_name = 'memberapp/member/form.html'
    success_url = reverse_lazy('memberapp:member_list')
    context_object_name = 'object'
    success_message = 'Member updated.'

    def get_queryset(self):
        return _member_queryset_for_viewer(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Member'
        rows, applied_ids = permission_matrix_rows_with_applied(self.object, effective=False)
        context['show_member_permissions'] = True
        context['permission_matrix_rows'] = rows
        context['applied_permission_ids'] = applied_ids
        context['permission_matrix_help'] = 'edit'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        selected = filter_valid_permission_ids(self.request.POST.getlist('user_perms'))
        self.object.user_permissions.set(selected)
        return response


class MemberDeleteView(AutoPermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'memberapp/common-html/delete.html'
    success_url = reverse_lazy('memberapp:member_list')
    context_object_name = 'object'

    def get_queryset(self):
        return _member_queryset_for_viewer(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context['title'] = 'Delete Employee'

        context['object_display'] = (
            f"{obj.username}" 
        )

         #  permission
        context['can_delete'] = self.request.user.has_perm(
            'memberapp.delete_member'
        )

        #  cancel button
        context['cancel_url'] = reverse('memberapp:member_list')
        return context


class MemberCopyView(AutoPermissionRequiredMixin, View):
    """Redirect to member create with initial data from the copied user."""

    def get(self, request, pk):
        from django.urls import reverse
        from urllib.parse import quote
        obj = get_object_or_404(_member_queryset_for_viewer(request.user), pk=pk)
        params = []
        if obj.team_id:
            params.append(f'team={obj.team_id}')
        if obj.department_id:
            params.append(f'department={obj.department_id}')
        if obj.designation_id:
            params.append(f'designation={obj.designation_id}')
        if obj.phone:
            params.append(f'phone={quote(obj.phone)}')
        if obj.discord_id:
           params.append(f'discord_id={quote(obj.discord_id)}')
        if obj.email_password:
           params.append(f'email_password={quote(obj.email_password)}')
        if obj.discord_password:
          params.append(f'discord_password={quote(obj.discord_password)}')
        if obj.employee_id:
            params.append(f'employee_id={quote(obj.employee_id)}')
        url = reverse('memberapp:member_create')
        if params:
            url = f'{url}?{"&".join(params)}'
        messages.info(request, 'Create a new member with pre-filled details.')
        return redirect(url)


def _style_set_password_form(form):
    """Strip conflicting widget classes; visibility comes from password_form.html scoped CSS."""
    for name in ('new_password1', 'new_password2'):
        if name in form.fields:
            form.fields[name].widget.attrs['class'] = 'password-form-input'
    return form


class MemberPasswordChangeView(PermissionRequiredMixin, View):
    """Admin/staff sets a member's password (no old password). Requires change_user."""
    permission_required = 'memberapp.change_user'

    def get(self, request, pk):
        member = get_object_or_404(_member_queryset_for_viewer(request.user), pk=pk)
        form = _style_set_password_form(MemberSetPasswordForm(member))
        return render(
            request,
            'memberapp/member/password_form.html',
            {
                'form': form,
                'title': f'Change password — {member.get_username()}',
                'member': member,
                'cancel_url': reverse('memberapp:member_list'),
            },
        )

    def post(self, request, pk):
        member = get_object_or_404(_member_queryset_for_viewer(request.user), pk=pk)
        form = _style_set_password_form(MemberSetPasswordForm(member, request.POST))
        if form.is_valid():
            form.save()
            messages.success(request, 'Password updated.')
            return redirect('memberapp:member_list')
        return render(
            request,
            'memberapp/member/password_form.html',
            {
                'form': form,
                'title': f'Change password — {member.get_username()}',
                'member': member,
                'cancel_url': reverse('memberapp:member_list'),
            },
        )

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView
from commonapp.mixin import AutoPermissionRequiredMixin
from commonapp.global_filters import apply_hardware_issue_filters
from commonapp.utils import get_datatables_params
from hardwareapp.models import (
    CabinetTable,
    GraphicsCardTable,
    HDDTable,
    HeadphoneTable,
    KeyboardTable,
    LiquidCoolerTable,
    MonitorTable,
    MotherboardTable,
    MouseTable,
    Pentable,
    PowerSupplyTable,
    ProcessorTable,
    RAMTable,
    SSDTable,
    SpeakerTable,
    UPSTable,
    WebcamTable,
)
from hardwareissueapp.models import HardwareIssueTable
from hardwareissueapp.summary_cards import hardware_issue_summary_cards


ISSUE_COMPONENT_MODEL_MAP = {
    'hardwareapp:processor_detail': ('processor', ProcessorTable),
    'hardwareapp:graphics_card_detail': ('graphics_card', GraphicsCardTable),
    'hardwareapp:motherboard_detail': ('motherboard', MotherboardTable),
    'hardwareapp:ram_detail': ('ram', RAMTable),
    'hardwareapp:hdd_detail': ('hdd', HDDTable),
    'hardwareapp:ssd_detail': ('ssd', SSDTable),
    'hardwareapp:liquid_cooler_detail': ('liquid_cooler', LiquidCoolerTable),
    'hardwareapp:ups_detail': ('ups', UPSTable),
    'hardwareapp:monitor_detail': ('monitor', MonitorTable),
    'hardwareapp:keyboard_detail': ('keyboard', KeyboardTable),
    'hardwareapp:mouse_detail': ('mouse', MouseTable),
    'hardwareapp:headphone_detail': ('headphone', HeadphoneTable),
    'hardwareapp:pentable_detail': ('pentable', Pentable),
    'hardwareapp:speaker_detail': ('speaker', SpeakerTable),
    'hardwareapp:webcam_detail': ('webcam', WebcamTable),
    'hardwareapp:power_supply_detail': ('power_supply', PowerSupplyTable),
    'hardwareapp:cabinet_detail': ('cabinet', CabinetTable),
}
ISSUE_MODEL_BY_TYPE = {val[0]: val[1] for val in ISSUE_COMPONENT_MODEL_MAP.values()}


class HardwareIssueCreateAPIView(AutoPermissionRequiredMixin, View):
    model = HardwareIssueTable

    def post(self, request, *args, **kwargs):
        component_route = (request.POST.get('component_route') or '').strip()
        component_id_raw = (request.POST.get('component_id') or '').strip()
        reason = (request.POST.get('reason') or '').strip()
        qty_raw = (request.POST.get('quantity') or '').strip()

        if component_route not in ISSUE_COMPONENT_MODEL_MAP:
            return JsonResponse({'error': 'Invalid component type.'}, status=400)
        try:
            component_id = int(component_id_raw)
            quantity = int(qty_raw)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Quantity and component id must be numbers.'}, status=400)
        if quantity <= 0:
            return JsonResponse({'error': 'Quantity must be at least 1.'}, status=400)
        if not reason:
            return JsonResponse({'error': 'Reason is required.'}, status=400)

        component_type, model_class = ISSUE_COMPONENT_MODEL_MAP[component_route]
        with transaction.atomic():
            obj = model_class.objects.select_for_update().filter(pk=component_id, is_delete=False).first()
            if not obj:
                return JsonResponse({'error': 'Component not found.'}, status=404)
            total_qty = int(getattr(obj, 'quantity', 0) or 0)
            assign = int(getattr(obj, 'assign', 0) or 0)
            remaining = int(getattr(obj, 'remaining', 0) or 0)
            current_issue = int(getattr(obj, 'issue', 0) or 0)
            available_by_total = max(total_qty - assign, 0)
            available = min(remaining, available_by_total) if remaining >= 0 else available_by_total

            if quantity > available:
                return JsonResponse(
                    {'error': f'Cannot issue {quantity}. Only {available} available.'},
                    status=400,
                )

            obj.assign = assign + quantity
            obj.remaining = max(total_qty - obj.assign, 0)
            obj.issue = current_issue + quantity
            obj.save(update_fields=['assign', 'remaining', 'issue', 'updated_at'])

            issue = HardwareIssueTable.objects.create(
                component_route=component_route,
                component_type=component_type,
                component_id=obj.pk,
                component_name=getattr(obj, 'name', '') or str(obj),
                team=getattr(obj, 'team', None),
                quantity=quantity,
                reason=reason,
                issued_by=request.user if request.user.is_authenticated else None,
            )
            issue_total = obj.issue

        return JsonResponse(
            {
                'ok': True,
                'issue_id': issue.pk,
                'total': total_qty,
                'assign': obj.assign,
                'remaining': obj.remaining,
                'issued_total': issue_total,
                'message': 'Hardware issued successfully.',
            }
        )


class HardwareIssueListView(AutoPermissionRequiredMixin, ListView):
    model = HardwareIssueTable
    template_name = 'hardwareissueapp/issue/list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        qs = super().get_queryset()
        return apply_hardware_issue_filters(qs, self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Hardware Issues'
        context['table_columns'] = ['Sl', 'Component', 'Type', 'Team', 'Quantity', 'Reason', 'Issued By', 'Issued At', 'Actions']
        context['summary_cards'] = hardware_issue_summary_cards(self.get_queryset())
        return context


class HardwareIssueListDataView(AutoPermissionRequiredMixin, View):
    model = HardwareIssueTable

    def get(self, request, *args, **kwargs):
        params = get_datatables_params(request)
        qs = HardwareIssueTable.objects.select_related('team', 'issued_by').filter(is_delete=False)
        qs = apply_hardware_issue_filters(qs, request)
        records_total = qs.count()
        if params['search_value']:
            sv = params['search_value']
            qs = qs.filter(
                Q(component_name__icontains=sv)
                | Q(component_type__icontains=sv)
                | Q(reason__icontains=sv)
                | Q(team__name__icontains=sv)
                | Q(issued_by__username__icontains=sv)
                | Q(issued_by__first_name__icontains=sv)
                | Q(issued_by__last_name__icontains=sv)
            )
        records_filtered = qs.count()
        order_cols = ['id', 'component_name', 'component_type', 'team__name', 'quantity', 'reason', 'issued_by__username', 'created_at']
        if 0 <= params['order_column'] < len(order_cols):
            order_prefix = '' if params['order_dir'] == 'asc' else '-'
            qs = qs.order_by(f'{order_prefix}{order_cols[params["order_column"]]}')
        else:
            qs = qs.order_by('-id')

        can_view = request.user.has_perm('hardwareissueapp.view_hardwareissue')
        can_revoke = request.user.has_perm('hardwareissueapp.change_hardwareissuetable')
        page = qs[params['start']:params['start'] + params['length']]
        data = []
        for idx, obj in enumerate(page):
            counter = params['start'] + idx + 1
            name_cell = render_to_string(
                'partials/cell_link_or_span.html',
                {'url_name': 'hardwareissueapp:issue_detail', 'pk': obj.pk, 'label': obj.component_name or '—', 'can_view': can_view},
                request=request,
            )
            actions_cell = render_to_string(
                'partials/row_actions.html',
                {
                    'detail_url_name': 'hardwareissueapp:issue_detail',
                    'update_url_name': 'hardwareissueapp:issue_detail',
                    'copy_url_name': 'hardwareissueapp:issue_detail',
                    'delete_url_name': 'hardwareissueapp:issue_revoke',
                    'delete_title': 'Revoke',
                    'obj': obj,
                    'can_view': can_view,
                    'can_edit': False,
                    'can_copy': False,
                    'can_delete': can_revoke,
                },
                request=request,
            )
            issued_by = (obj.issued_by.get_full_name() or '').strip() if obj.issued_by else ''
            if not issued_by:
                issued_by = obj.issued_by.username if obj.issued_by else '—'
            data.append(
                [
                    counter,
                    name_cell,
                    obj.component_type.replace('_', ' ').title(),
                    obj.team.name if obj.team else '—',
                    obj.quantity,
                    obj.reason,
                    issued_by,
                    obj.created_at.strftime('%Y-%m-%d %H:%M'),
                    actions_cell,
                ]
            )

        return JsonResponse(
            {
                'draw': params['draw'],
                'recordsTotal': records_total,
                'recordsFiltered': records_filtered,
                'data': data,
            }
        )


class HardwareIssueDetailView(AutoPermissionRequiredMixin, DetailView):
    model = HardwareIssueTable
    template_name = 'hardwareissueapp/common-html/details.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        issued_by = (obj.issued_by.get_full_name() or '').strip() if obj.issued_by else ''
        if not issued_by:
            issued_by = obj.issued_by.username if obj.issued_by else '—'
        context['title'] = f'Issue #{obj.pk}'
        context['fields'] = [
            {'label': 'Component', 'value': obj.component_name},
            {'label': 'Type', 'value': obj.component_type.replace('_', ' ').title()},
            {'label': 'Quantity', 'value': obj.quantity},
            {'label': 'Team', 'value': obj.team.name if obj.team else '—'},
            {'label': 'Reason', 'value': obj.reason},
            {'label': 'Issued By', 'value': issued_by},
            {'label': 'Issued At', 'value': obj.created_at.strftime('%Y-%m-%d %H:%M')},
        ]
        context['list_url'] = reverse('hardwareissueapp:issue_list')
        context['can_edit'] = False
        context['can_delete'] = False
        return context


class HardwareIssueRevokeView(AutoPermissionRequiredMixin, View):
    model = HardwareIssueTable

    def _apply_revoke(self, issue, revoke_qty):
        model_class = ISSUE_MODEL_BY_TYPE.get(issue.component_type)
        with transaction.atomic():
            if model_class is not None:
                obj = model_class.objects.select_for_update().filter(pk=issue.component_id, is_delete=False).first()
                if obj is not None:
                    total_qty = int(getattr(obj, 'quantity', 0) or 0)
                    assign = int(getattr(obj, 'assign', 0) or 0)
                    issue_qty = int(getattr(obj, 'issue', 0) or 0)
                    obj.assign = max(assign - revoke_qty, 0)
                    obj.issue = max(issue_qty - revoke_qty, 0)
                    obj.remaining = max(total_qty - obj.assign, 0)
                    obj.save(update_fields=['assign', 'issue', 'remaining', 'updated_at'])

            issue.quantity = max(int(issue.quantity or 0) - revoke_qty, 0)
            if issue.quantity <= 0:
                issue.is_delete = True
                issue.save(update_fields=['quantity', 'is_delete', 'updated_at'])
            else:
                issue.save(update_fields=['quantity', 'updated_at'])

    def get(self, request, pk):
        issue = get_object_or_404(HardwareIssueTable, pk=pk, is_delete=False)
        revoke_qty = int(issue.quantity or 0)
        self._apply_revoke(issue, revoke_qty)
        return redirect('hardwareissueapp:issue_list')

    def post(self, request, pk):
        issue = get_object_or_404(HardwareIssueTable, pk=pk, is_delete=False)
        qty_raw = (request.POST.get('quantity') or '').strip()
        try:
            revoke_qty = int(qty_raw)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Quantity must be a number.'}, status=400)
        if revoke_qty <= 0:
            return JsonResponse({'error': 'Quantity must be at least 1.'}, status=400)
        if revoke_qty > int(issue.quantity or 0):
            return JsonResponse({'error': f'Cannot revoke {revoke_qty}. Maximum allowed is {issue.quantity}.'}, status=400)

        self._apply_revoke(issue, revoke_qty)
        return JsonResponse(
            {
                'ok': True,
                'message': 'Hardware revoke successful.',
                'remaining_issue_qty': int(issue.quantity or 0),
                'team': issue.team.name if issue.team else '—',
            }
        )

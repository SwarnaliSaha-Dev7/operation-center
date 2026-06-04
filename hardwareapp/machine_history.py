"""Helpers to record and format machine history (used by signals and machine save)."""
import re

from django.contrib.auth import get_user_model

from commonapp.utils import get_current_user

User = get_user_model()


def _user_label(user):
    if not user:
        return '—'
    name = (user.get_full_name() or '').strip()
    if name:
        return f'{name} ({user.username})'
    return user.username or '—'


def _component_line(label, quantities):
    if not quantities:
        return None
    parts = []
    for comp, qty in quantities:
        if comp is None:
            continue
        name = getattr(comp, 'name', None) or str(comp)
        parts.append(f'{name} ×{qty}')
    if not parts:
        return None
    return f'{label}: {", ".join(parts)}'


def build_machine_components_summary(machine):
    """Human-readable multi-line summary of attached hardware (OS is logged separately)."""
    lines = []
    sections = [
        ('Processor(s)', machine.get_processor_quantities()),
        ('RAM', machine.get_ram_quantities()),
        ('SSD(s)', machine.get_ssd_quantities()),
        ('Motherboard(s)', machine.get_motherboard_quantities()),
        ('Power supply', machine.get_power_supply_quantities()),
        ('Cabinet(s)', machine.get_cabinet_quantities()),
        ('Liquid cooler(s)', machine.get_liquid_cooler_quantities()),
        ('Graphics card(s)', machine.get_graphics_card_quantities()),
        ('HDD(s)', machine.get_hdd_quantities()),
        ('UPS', machine.get_ups_quantities()),
        ('Monitor(s)', machine.get_monitor_quantities()),
        ('Keyboard(s)', machine.get_keyboard_quantities()),
        ('Mouse', machine.get_mouse_quantities()),
        ('Headphone(s)', machine.get_headphone_quantities()),
        ('Desk / Pen table(s)', machine.get_pentable_quantities()),
        ('Speaker(s)', machine.get_speaker_quantities()),
        ('Webcam(s)', machine.get_webcam_quantities()),
    ]
    for title, rows in sections:
        line = _component_line(title, rows)
        if line:
            lines.append(line)
    return '\n'.join(lines) if lines else 'No hardware rows recorded yet.'


def hardware_summary_to_rows(summary: str):
    """
    Split build_machine_components_summary() text into rows for compact UI cards.
    Each row is {'label': str, 'value': str} where label is the part before ':'.
    """
    rows = []
    text = (summary or '').strip()
    if not text:
        return rows
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label, _, value = line.partition(':')
            rows.append({'label': label.strip(), 'value': value.strip()})
        else:
            rows.append({'label': '', 'value': line})
    return rows


_SKIP_HW_INSTANCE_FIELDS = frozenset(
    {
        'id',
        'team',
        'createdby',
        'updatedby',
        'is_delete',
        'created_at',
        'updated_at',
        # Pool / stock columns — not shown on member machine activity cards
        'quantity',
        'assign',
        'remaining',
        'issue',
    }
)


def _hardware_instance_field_rows(instance):
    """Label/value pairs from a hardware inventory model instance (full table row)."""
    from django.db import models as dj_models

    rows = []
    for field in instance._meta.fields:
        if field.name in _SKIP_HW_INSTANCE_FIELDS:
            continue
        raw = getattr(instance, field.name)
        if isinstance(field, dj_models.BooleanField):
            value = 'Yes' if raw else 'No'
        elif raw is None or raw == '':
            value = '—'
        else:
            value = raw
        label = field.verbose_name.title() if field.verbose_name else field.name.replace('_', ' ').title()
        rows.append({'label': str(label), 'value': value})
    return rows


def machine_hardware_part_cards(machine):
    """
    One card per attached component: section title + qty on machine + all DB columns
    from the inventory table row (processor, ram, ssd, …).
    """
    sections = [
        ('Processor(s)', machine.get_processor_quantities),
        ('RAM', machine.get_ram_quantities),
        ('SSD(s)', machine.get_ssd_quantities),
        ('Motherboard(s)', machine.get_motherboard_quantities),
        ('Power supply', machine.get_power_supply_quantities),
        ('Cabinet(s)', machine.get_cabinet_quantities),
        ('Liquid cooler(s)', machine.get_liquid_cooler_quantities),
        ('Graphics card(s)', machine.get_graphics_card_quantities),
        ('HDD(s)', machine.get_hdd_quantities),
        ('UPS', machine.get_ups_quantities),
        ('Monitor(s)', machine.get_monitor_quantities),
        ('Keyboard(s)', machine.get_keyboard_quantities),
        ('Mouse', machine.get_mouse_quantities),
        ('Headphone(s)', machine.get_headphone_quantities),
        ('Desk / Pen table(s)', machine.get_pentable_quantities),
        ('Speaker(s)', machine.get_speaker_quantities),
        ('Webcam(s)', machine.get_webcam_quantities),
    ]
    cards = []
    for section_title, getter in sections:
        pairs = getter()
        for comp, qty in pairs:
            if comp is None:
                continue
            field_rows = _hardware_instance_field_rows(comp)
            team = getattr(comp, 'team', None)
            if team is not None:
                field_rows.insert(0, {'label': 'Team', 'value': getattr(team, 'name', '—')})
            field_rows.insert(
                0,
                {'label': 'Quantity on this machine', 'value': qty},
            )
            cards.append(
                {
                    'section': section_title,
                    'fields': field_rows,
                }
            )
    return cards


def _parse_sections(text):
    """Map section title (before first ':') to the rest of the line."""
    out = {}
    if not text or not text.strip():
        return out
    if text.strip() == 'No hardware rows recorded yet.':
        return out
    for line in text.strip().split('\n'):
        if ':' not in line:
            continue
        title, rest = line.split(':', 1)
        out[title.strip()] = rest.strip()
    return out


def _sum_quantities(section_value):
    """Sum all ×qty numbers in a section value string."""
    if not section_value:
        return 0
    total = 0
    for m in re.finditer(r'×\s*(\d+)', section_value):
        total += int(m.group(1))
    return total


def _short_label(section_title):
    return section_title.replace('(s)', '').strip()


def _classify_change(old_val, new_val):
    """
    Return kind: added | removed | upgrade | downgrade | changed
    old_val/new_val are the text after 'Label: ' (component list).
    """
    old_val = (old_val or '').strip()
    new_val = (new_val or '').strip()
    if not old_val and new_val:
        return 'added'
    if old_val and not new_val:
        return 'removed'
    if old_val == new_val:
        return None
    oq, nq = _sum_quantities(old_val), _sum_quantities(new_val)
    if nq > oq:
        return 'upgrade'
    if nq < oq:
        return 'downgrade'
    return 'changed'


def _diff_hardware(prev_snapshot, new_snapshot):
    """
    Compare two full snapshots. Returns (changes, headline, change_tone).
    changes: list of dicts with section, kind, old, new
    change_tone: initial | upgrade | downgrade | replacement | mixed
    """
    old_map = _parse_sections(prev_snapshot) if prev_snapshot else {}
    new_map = _parse_sections(new_snapshot) if new_snapshot else {}
    all_keys = sorted(set(old_map) | set(new_map))

    changes = []
    for key in all_keys:
        o, n = old_map.get(key), new_map.get(key)
        if o == n:
            continue
        kind = _classify_change(o, n)
        if kind is None:
            continue
        changes.append({'section': key, 'kind': kind, 'old': o or '—', 'new': n or '—'})

    if not changes:
        return [], 'Hardware configuration unchanged.', 'neutral'

    if not old_map:
        headline = 'Initial hardware configuration'
        tone = 'initial'
        return changes, headline, tone

    up_labels = [_short_label(c['section']) for c in changes if c['kind'] in ('added', 'upgrade')]
    down_labels = [_short_label(c['section']) for c in changes if c['kind'] in ('removed', 'downgrade')]
    neu_labels = [_short_label(c['section']) for c in changes if c['kind'] == 'changed']

    has_up, has_down, has_neu = bool(up_labels), bool(down_labels), bool(neu_labels)

    if has_up and not has_down and not has_neu:
        headline = f'Upgrade — {", ".join(up_labels)}'
        tone = 'upgrade'
    elif has_down and not has_up and not has_neu:
        headline = f'Downgrade — {", ".join(down_labels)}'
        tone = 'downgrade'
    elif has_neu and not has_up and not has_down:
        headline = f'Component replacement — {", ".join(neu_labels)}'
        tone = 'replacement'
    else:
        parts = []
        if up_labels:
            parts.append(f'upgrade: {", ".join(up_labels)}')
        if down_labels:
            parts.append(f'downgrade: {", ".join(down_labels)}')
        if neu_labels:
            parts.append(f'replaced: {", ".join(neu_labels)}')
        headline = 'Mixed hardware update — ' + '; '.join(parts)
        tone = 'mixed'

    return changes, headline, tone


def _format_diff_lines(changes, is_initial):
    """Human-readable diff only (no full inventory)."""
    lines = []
    for c in changes:
        sec = c['section']
        if is_initial:
            lines.append(f'+ {sec}: {c["new"]}')
        elif c['kind'] == 'added':
            lines.append(f'+ {sec}: {c["new"]}')
        elif c['kind'] == 'removed':
            lines.append(f'− {sec}: {c["old"]}')
        else:
            lines.append(f'• {sec}')
            lines.append(f'  Before: {c["old"]}')
            lines.append(f'  After:  {c["new"]}')
    return '\n'.join(lines)


def _actor():
    u = get_current_user()
    if u and u.is_authenticated:
        return u
    return None


def log_machine_created(machine):
    from hardwareapp.models import MachineHistoryEntry

    meta = {
        'name': machine.name,
        'code': machine.code,
        'team': machine.team.name if machine.team_id else None,
        'department': machine.department.name if machine.department_id else None,
        'initial_member': _user_label(machine.member) if machine.member_id else None,
    }
    summary = (
        f'Machine created'
        f' ({machine.name or "—"} / {machine.code or "—"})'
    )
    if machine.member_id:
        summary += f'. Initial assignee: {_user_label(machine.member)}.'
    MachineHistoryEntry.objects.create(
        machine=machine,
        event_type=MachineHistoryEntry.EventType.MACHINE_CREATED,
        summary=summary,
        metadata=meta,
        created_by=_actor(),
    )


def log_member_changed(machine, old_member_id, new_member_id):
    from hardwareapp.models import MachineHistoryEntry

    old_u = User.objects.filter(pk=old_member_id).first() if old_member_id else None
    new_u = User.objects.filter(pk=new_member_id).first() if new_member_id else None
    meta = {
        'from_user_id': old_member_id,
        'to_user_id': new_member_id,
        'from_label': _user_label(old_u) if old_u else 'Unassigned',
        'to_label': _user_label(new_u) if new_u else 'Unassigned',
    }
    if old_u is None and new_u is not None:
        summary = f'Assigned to {_user_label(new_u)}.'
    elif old_u is not None and new_u is None:
        summary = f'Unassigned (was {_user_label(old_u)}).'
    elif old_u is not None and new_u is not None and old_u.pk != new_u.pk:
        summary = f'Reassigned from {_user_label(old_u)} to {_user_label(new_u)}.'
    else:
        return
    MachineHistoryEntry.objects.create(
        machine=machine,
        event_type=MachineHistoryEntry.EventType.MEMBER_CHANGED,
        summary=summary,
        metadata=meta,
        created_by=_actor(),
    )


def log_os_changed(machine, action, os_ids):
    from hardwareapp.models import MachineHistoryEntry, OperatingSystemTable

    if not os_ids and action != 'post_clear':
        return
    if action == 'post_clear':
        summary = 'All operating system links removed from this machine.'
        meta = {'action': 'clear', 'assignee_id': machine.member_id}
    else:
        qs = OperatingSystemTable.objects.filter(pk__in=os_ids)
        names = []
        for o in qs:
            ver = getattr(o, 'version', None) or ''
            nm = getattr(o, 'name', None) or str(o)
            names.append(f'{nm} ({ver})' if ver else nm)
        verb = 'Added' if action == 'post_add' else 'Removed'
        summary = f'{verb} operating system(s): {", ".join(names) if names else "—"}.'
        meta = {'action': action, 'os_ids': list(os_ids), 'assignee_id': machine.member_id}
    MachineHistoryEntry.objects.create(
        machine=machine,
        event_type=MachineHistoryEntry.EventType.OS_CHANGED,
        summary=summary,
        metadata=meta,
        created_by=_actor(),
    )


def log_components_snapshot(machine):
    """After through-rows are saved: log only diffs vs previous snapshot; skip if unchanged."""
    from hardwareapp.models import MachineHistoryEntry

    machine.refresh_from_db()
    current = build_machine_components_summary(machine)

    prev_entry = (
        MachineHistoryEntry.objects.filter(
            machine=machine,
            event_type=MachineHistoryEntry.EventType.COMPONENTS_UPDATED,
        )
        .order_by('-created_at')
        .first()
    )
    prev_meta = (prev_entry.metadata or {}) if prev_entry else {}
    # Prefer stored full_snapshot; fall back to legacy `detail` for rows logged before diff-based history.
    prev_snapshot = prev_meta.get('full_snapshot') or prev_meta.get('detail')

    if prev_snapshot is not None and prev_snapshot == current:
        return

    changes, headline, change_tone = _diff_hardware(prev_snapshot, current)
    if not changes:
        return

    is_initial = change_tone == 'initial'

    diff_text = _format_diff_lines(changes, is_initial=is_initial)
    if not diff_text.strip():
        diff_text = '(No component lines to show.)'

    meta = {
        'full_snapshot': current,
        'diff': diff_text,
        'change_tone': change_tone,
        'changes': changes,
        'assignee_id': machine.member_id,
    }

    MachineHistoryEntry.objects.create(
        machine=machine,
        event_type=MachineHistoryEntry.EventType.COMPONENTS_UPDATED,
        summary=headline,
        metadata=meta,
        created_by=_actor(),
    )


def member_machine_activity_data(user):
    """
    Aggregates and timeline for one member: assignments, hardware changes, and OS changes
    attributed to them via metadata.assignee_id (set on new logs). Assignment rows use
    metadata.from_user_id / to_user_id.
    """
    from django.db.models import Q

    from hardwareapp.models import MachineHistoryEntry, MachineTable

    uid = user.pk
    ET = MachineHistoryEntry.EventType

    assignment_qs = (
        MachineHistoryEntry.objects.filter(event_type=ET.MEMBER_CHANGED)
        .filter(Q(metadata__to_user_id=uid) | Q(metadata__from_user_id=uid))
        .select_related('machine', 'created_by')
    )

    assignee_hw = Q(metadata__assignee_id=uid)
    hw_qs = (
        MachineHistoryEntry.objects.filter(event_type=ET.COMPONENTS_UPDATED)
        .filter(assignee_hw)
        .select_related('machine', 'created_by')
    )
    os_qs = (
        MachineHistoryEntry.objects.filter(event_type=ET.OS_CHANGED)
        .filter(assignee_hw)
        .select_related('machine', 'created_by')
    )

    received = MachineHistoryEntry.objects.filter(
        event_type=ET.MEMBER_CHANGED,
        metadata__to_user_id=uid,
    ).count()
    released = MachineHistoryEntry.objects.filter(
        event_type=ET.MEMBER_CHANGED,
        metadata__from_user_id=uid,
    ).exclude(metadata__to_user_id=uid).count()

    tone_counts = {'upgrade': 0, 'downgrade': 0, 'mixed': 0, 'replacement': 0, 'initial': 0, 'neutral': 0}
    for row in hw_qs.values_list('metadata', flat=True):
        tone = (row or {}).get('change_tone') or 'neutral'
        if tone in tone_counts:
            tone_counts[tone] += 1
        else:
            tone_counts['neutral'] += 1

    machine_ids_assign = set(assignment_qs.values_list('machine_id', flat=True))
    machine_ids_current = set(
        MachineTable.objects.filter(member=user, is_delete=False).values_list('pk', flat=True)
    )
    unique_machines_touched = len(machine_ids_assign | machine_ids_current)

    timeline = list(assignment_qs) + list(hw_qs) + list(os_qs)
    timeline.sort(key=lambda e: e.created_at, reverse=True)

    assigned_machines = []
    machines_qs = (
        MachineTable.objects.filter(member=user, is_delete=False)
        .select_related('team', 'department')
        .prefetch_related('operating_system')
        .order_by('name', 'code', 'pk')
    )
    for m in machines_qs:
        os_list = list(m.operating_system.all())
        os_parts = []
        for o in os_list:
            n = (getattr(o, 'name', None) or '').strip()
            v = (getattr(o, 'version', None) or '').strip()
            os_parts.append(f'{n} {v}'.strip() if v else (n or '—'))
        summary = build_machine_components_summary(m)
        assigned_machines.append(
            {
                'machine': m,
                'os_display': ', '.join(os_parts) if os_parts else '—',
                'components_summary': summary,
                'hardware_rows': hardware_summary_to_rows(summary),
                'hardware_part_cards': machine_hardware_part_cards(m),
            }
        )

    return {
        'assigned_machines': assigned_machines,
        'stats': {
            'current_systems': MachineTable.objects.filter(member=user, is_delete=False).count(),
            'unique_machines_ever': unique_machines_touched,
            'assignment_events': assignment_qs.count(),
            'times_received_machine': received,
            'times_released_machine': released,
            'hardware_events_as_assignee': hw_qs.count(),
            'os_events_as_assignee': os_qs.count(),
            **{f'hardware_{k}': v for k, v in tone_counts.items()},
        },
        'timeline': timeline,
    }

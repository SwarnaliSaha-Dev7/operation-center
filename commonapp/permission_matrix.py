"""Build model permission matrix rows for member create UI (Django auth permissions)."""
from django.apps import apps as django_apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Local apps whose models appear in the member permission table
PERMISSION_MATRIX_APPS = (
    'dashboardapp',
    'hardwareapp',
    'commonapp',
    'memberapp',
    'hardwareissueapp',
    'ticketingapp',
)

# Tailwind classes: distinct row backgrounds per app group (order of first appearance)
_APP_GROUP_ROW_CLASSES = (
    'bg-slate-200/90 hover:bg-slate-300/80',
    'bg-blue-100/95 hover:bg-blue-200/85',
    'bg-emerald-100/95 hover:bg-emerald-200/85',
    'bg-amber-100/95 hover:bg-amber-200/85',
    'bg-violet-100/95 hover:bg-violet-200/85',
    'bg-cyan-100/95 hover:bg-cyan-200/85',
    'bg-rose-100/95 hover:bg-rose-200/85',
    'bg-indigo-100/95 hover:bg-indigo-200/85',
)


def _app_display_name(app_label: str) -> str:
    try:
        return str(django_apps.get_app_config(app_label).verbose_name)
    except LookupError:
        return app_label


def permission_matrix_rows():
    """
    One row per concrete model (excluding *through* M2M join models), with view/add/change/delete
    Permission objects plus any custom Meta.permissions (e.g. ticketingapp.manage_it_tickets).
    """
    rows = []
    for ct in (
        ContentType.objects.filter(app_label__in=PERMISSION_MATRIX_APPS)
        .order_by('app_label', 'model')
        .select_related()
    ):
        model = ct.model_class()
        model_name = (model._meta.model_name if model is not None else ct.model)
        if model_name.endswith('through'):
            continue
        perms = {}
        extras = []
        for p in Permission.objects.filter(content_type=ct).order_by('name'):
            if p.codename.startswith('add_'):
                perms['add'] = p
            elif p.codename.startswith('change_'):
                perms['change'] = p
            elif p.codename.startswith('delete_'):
                perms['delete'] = p
            elif p.codename.startswith('view_'):
                perms['view'] = p
            else:
                extras.append(p)
        rows.append(
            {
                'app_label': ct.app_label,
                'app_name': _app_display_name(ct.app_label),
                'table_name': (
                    str(model._meta.verbose_name).title()
                    if model is not None
                    else str(ct.model).replace('_', ' ').title()
                ),
                'model_name': model_name,
                'view': perms.get('view'),
                'add': perms.get('add'),
                'edit': perms.get('change'),
                'delete': perms.get('delete'),
                'extras': extras,
            }
        )

    # App-wise background: same color for all rows of an app
    app_index = {}
    for row in rows:
        label = row['app_label']
        if label not in app_index:
            app_index[label] = len(app_index)
        palette_i = app_index[label] % len(_APP_GROUP_ROW_CLASSES)
        row['group_row_class'] = _APP_GROUP_ROW_CLASSES[palette_i]

    return rows


def _collect_perm_pks(row):
    for p in (row.get('view'), row.get('add'), row.get('edit'), row.get('delete')):
        if p:
            yield p
    for p in row.get('extras') or ():
        if p:
            yield p


def _applied_permission_ids_for_rows(user, rows, effective=True):
    """Which matrix permission PKs apply: effective (user + groups via has_perm) or direct user_permissions only."""
    ids = set()

    if effective:
        for row in rows:
            for p in _collect_perm_pks(row):
                if user.has_perm(f'{p.content_type.app_label}.{p.codename}'):
                    ids.add(p.pk)
    else:
        direct = set(user.user_permissions.values_list('pk', flat=True))
        for row in rows:
            for p in _collect_perm_pks(row):
                if p.pk in direct:
                    ids.add(p.pk)
    return ids


def permission_matrix_rows_with_applied_for_group(group):
    """Matrix rows and permission PKs assigned to this auth Group (role)."""
    rows = permission_matrix_rows()
    allowed = set(group.permissions.values_list('pk', flat=True))
    applied_ids = set()
    for row in rows:
        for p in _collect_perm_pks(row):
            if p.pk in allowed:
                applied_ids.add(p.pk)
    return rows, applied_ids


def permission_matrix_rows_with_applied(user, effective=True):
    """Build matrix rows and the set of applied permission primary keys for checkboxes."""
    rows = permission_matrix_rows()
    applied_ids = _applied_permission_ids_for_rows(user, rows, effective=effective)
    return rows, applied_ids


def filter_valid_permission_ids(permission_ids):
    """Return a queryset of Permission instances for the matrix apps and given primary keys."""
    ids = []
    for x in permission_ids:
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            continue
    if not ids:
        return Permission.objects.none()
    return Permission.objects.filter(
        pk__in=ids,
        content_type__app_label__in=PERMISSION_MATRIX_APPS,
    )

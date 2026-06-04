import threading


_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    _thread_locals.user = user


def get_datatables_params(request):
    """Parse DataTables server-side GET parameters."""
    return {
        'draw': int(request.GET.get('draw', 1)),
        'start': int(request.GET.get('start', 0)),
        'length': int(request.GET.get('length', 10)) or 10,
        'search_value': (request.GET.get('search[value]') or '').strip(),
        'order_column': int(request.GET.get('order[0][column]', 0)),
        'order_dir': request.GET.get('order[0][dir]', 'asc'),
    }
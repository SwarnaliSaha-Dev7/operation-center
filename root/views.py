from django.shortcuts import render


def _render_4xx(request, status_code, title, message):
    return render(
        request,
        "error/4xx.html",
        {"status_code": status_code, "title": title, "message": message},
        status=status_code,
    )


def handler400(request, exception):
    return _render_4xx(
        request,
        400,
        "Bad Request",
        "The request could not be understood or was invalid.",
    )


def handler403(request, exception):
    return _render_4xx(
        request,
        403,
        "Forbidden",
        "You do not have permission to access this page.",
    )


def handler404(request, exception):
    return _render_4xx(
        request,
        404,
        "Page Not Found",
        "The page you are looking for does not exist or has been moved.",
    )


def handler500(request):
    return render(
        request,
        "error/5xx.html",
        {
            "title": "Server Error",
            "message": "Something went wrong. Please try again later.",
        },
        status=500,
    )

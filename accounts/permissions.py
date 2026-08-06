from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def user_is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.is_system_admin())


def require_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_system_admin():
            messages.error(request, 'Se requieren permisos de administrador.')
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_perm(codename: str, app_label: str | None = None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.has_perm_codename(codename, app_label):
                messages.error(request, 'No tienes permiso para esta acción.')
                return redirect('core:dashboard')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

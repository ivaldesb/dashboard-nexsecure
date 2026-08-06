from django.utils import timezone


def sidebar(request):
    user = getattr(request, 'user', None)
    is_admin = bool(user and user.is_authenticated and user.is_system_admin())
    is_cliente = bool(
        user and user.is_authenticated and hasattr(user, 'cliente_profile') and user.cliente_profile is not None
    )
    return {
        'sidebar_is_admin': is_admin,
        'sidebar_is_cliente': is_cliente,
        'sidebar_now': timezone.now(),
    }

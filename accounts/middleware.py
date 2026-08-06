from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """Redirect anonymous users to login. Exempt: static, media, login."""

    EXEMPT_PREFIXES = ('/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        if not request.user.is_authenticated:
            login_path = reverse(settings.LOGIN_URL) if ':' in settings.LOGIN_URL else settings.LOGIN_URL
            if path != login_path and not path.startswith(login_path + '?'):
                return redirect(f'{login_path}?next={path}')

        return self.get_response(request)

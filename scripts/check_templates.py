# Chequeo mínimo: los templates nuevos compilan sin errores de sintaxis.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template.loader import get_template  # noqa: E402

TEMPLATES = [
    'base.html',
    'includes/sidebar.html',
    'accounts/login.html',
    'accounts/user_list.html',
    'accounts/user_form.html',
    'accounts/role_list.html',
    'accounts/role_form.html',
    'core/dashboard.html',
    'proyectos/detail.html',
]

for name in TEMPLATES:
    get_template(name)
    print(f'OK  {name}')

print('Todos los templates compilan.')

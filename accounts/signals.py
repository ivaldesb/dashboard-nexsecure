def seed_admin_role(sender, **kwargs):
    from accounts.models import Role

    Role.objects.get_or_create(
        name='admin',
        defaults={
            'description': 'Administrador con acceso total',
            'is_admin': True,
        },
    )

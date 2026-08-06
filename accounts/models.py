from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class Role(models.Model):
    name = models.CharField('nombre', max_length=100, unique=True)
    description = models.TextField('descripción', blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_admin = models.BooleanField(
        'administrador',
        default=False,
        help_text='Si es True, ve y gestiona todo el sistema.',
    )

    class Meta:
        verbose_name = 'rol'
        verbose_name_plural = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    tag = models.CharField('tag', max_length=64, blank=True, db_index=True)
    roles = models.ManyToManyField(Role, blank=True, related_name='users')

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def has_role(self, name: str) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(name=name).exists()

    def is_system_admin(self) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(is_admin=True).exists()

    def has_perm_codename(self, codename: str, app_label: str | None = None) -> bool:
        if self.is_system_admin():
            return True
        qs = Permission.objects.filter(codename=codename, roles__users=self)
        if app_label:
            qs = qs.filter(content_type__app_label=app_label)
        return qs.exists() or self.has_perm(f'{app_label}.{codename}' if app_label else codename)

    def role_names(self) -> str:
        return ', '.join(self.roles.values_list('name', flat=True)) or ('admin' if self.is_system_admin() else '')

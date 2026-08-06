from django.conf import settings
from django.db import models


class CategoriaDocumento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría de documento'
        verbose_name_plural = 'categorías de documento'

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='documentos')
    categoria = models.ForeignKey(
        CategoriaDocumento,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='documentos',
    )
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='documentos/')
    visible_cliente = models.BooleanField(
        default=False,
        help_text='Si True, los clientes del proyecto pueden verlo.',
    )
    solo_admin = models.BooleanField(
        default=False,
        help_text='Si True, solo administradores del sistema pueden acceder.',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='documentos_subidos',
    )
    users_allowed = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='documentos_permitidos',
        help_text='Usuarios adicionales con acceso (además de admin y uploader).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo

    def user_can_access(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.is_system_admin():
            return True
        if self.solo_admin:
            return False
        if self.uploaded_by_id == user.pk:
            return True
        if self.users_allowed.filter(pk=user.pk).exists():
            return True
        cliente = getattr(user, 'cliente_profile', None)
        if cliente is not None:
            return self.visible_cliente and self.proyecto.clientes.filter(pk=cliente.pk).exists()
        # Equipo del proyecto ve documentos subidos por un cliente del proyecto.
        uploader = self.uploaded_by
        uploader_cliente = getattr(uploader, 'cliente_profile', None) if uploader else None
        if uploader_cliente is not None and self.proyecto.clientes.filter(pk=uploader_cliente.pk).exists():
            return self.proyecto.equipo.filter(pk=user.pk).exists()
        return False


class DocumentoAudit(models.Model):
    VIEW = 'view'
    DOWNLOAD = 'download'
    ACTION_CHOICES = [
        (VIEW, 'Visualización'),
        (DOWNLOAD, 'Descarga'),
    ]

    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='audits')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} — {self.documento}'

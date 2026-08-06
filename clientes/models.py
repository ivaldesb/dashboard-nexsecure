from django.conf import settings
from django.db import models


class Cliente(models.Model):
    TIPO_PERSONA = 'persona'
    TIPO_EMPRESA = 'empresa'
    TIPO_CHOICES = [
        (TIPO_PERSONA, 'Persona'),
        (TIPO_EMPRESA, 'Empresa'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_EMPRESA)
    rut = models.CharField(max_length=20, blank=True)
    nombre = models.CharField(max_length=120, blank=True)
    apellido = models.CharField(max_length=120, blank=True)
    nombre_empresa = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    giro = models.CharField(max_length=200, blank=True)
    comuna = models.CharField(max_length=120, blank=True)
    ciudad = models.CharField(max_length=120, blank=True)
    activo = models.BooleanField(default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cliente_profile',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['nombre_empresa', 'apellido', 'nombre']

    def __str__(self):
        if self.tipo == self.TIPO_EMPRESA and self.nombre_empresa:
            return self.nombre_empresa
        return f'{self.nombre} {self.apellido}'.strip() or self.email or f'Cliente #{self.pk}'

    @property
    def display_name(self):
        return str(self)

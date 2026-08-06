from django.conf import settings
from django.db import models


class CategoriaActivo(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = 'categoría de activo'
        verbose_name_plural = 'categorías de activo'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Activo(models.Model):
    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='activos')
    categoria = models.ForeignKey(
        CategoriaActivo, null=True, blank=True, on_delete=models.SET_NULL, related_name='activos',
    )
    nombre = models.CharField(max_length=200)
    username = models.CharField(max_length=120, blank=True, verbose_name='usuario equipo')
    password = models.CharField(max_length=120, blank=True, verbose_name='contraseña')
    ip = models.CharField(max_length=64, blank=True)
    ip_dominio = models.CharField(max_length=200, blank=True, verbose_name='IP / dominio')
    ubicacion = models.CharField(max_length=200, blank=True, verbose_name='ubicación')
    sn = models.CharField(max_length=120, blank=True, verbose_name='número de serie')
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activos_asignados',
        verbose_name='técnico',
    )
    fecha_instalacion = models.DateField(null=True, blank=True)
    fecha_compra = models.DateField(null=True, blank=True)
    factura_boleta = models.CharField(max_length=120, blank=True, verbose_name='factura/boleta')
    archivo_compra = models.FileField(upload_to='activos/', null=True, blank=True)
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='activos_creados',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'activo'
        verbose_name_plural = 'activos'
        ordering = ['-updated_at']

    def __str__(self):
        return self.nombre

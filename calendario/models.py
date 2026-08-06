from django.conf import settings
from django.db import models


class CapaCalendario(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='capas_calendario',
    )
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default='#3498db')
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'capa de calendario'
        verbose_name_plural = 'capas de calendario'

    def __str__(self):
        return f'{self.nombre} ({self.user})'


class Evento(models.Model):
    TIPO_REUNION = 'reunion'
    TIPO_VISITA = 'visita'
    TIPO_OTRO = 'otro'
    TIPO_CHOICES = (
        (TIPO_REUNION, 'Reunión'),
        (TIPO_VISITA, 'Visita'),
        (TIPO_OTRO, 'Otro'),
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_OTRO)
    ubicacion = models.CharField(max_length=255, blank=True)
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eventos_creados',
    )
    proyecto = models.ForeignKey(
        'proyectos.Proyecto',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='eventos',
    )
    capa = models.ForeignKey(
        CapaCalendario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='eventos',
    )
    asignados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='eventos_asignados',
        help_text='Usuarios suscritos al evento (asignación manual; el creador se auto-asigna).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['inicio']

    def __str__(self):
        return self.titulo


class Tarea(models.Model):
    PRIORIDAD_BAJA = 'baja'
    PRIORIDAD_MEDIA = 'media'
    PRIORIDAD_ALTA = 'alta'
    PRIORIDAD_CHOICES = (
        (PRIORIDAD_BAJA, 'Baja'),
        (PRIORIDAD_MEDIA, 'Media'),
        (PRIORIDAD_ALTA, 'Alta'),
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default=PRIORIDAD_MEDIA)
    deadline = models.DateField()
    asignados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='tareas_asignadas',
    )
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tareas_creadas',
    )
    proyecto = models.ForeignKey(
        'proyectos.Proyecto',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tareas',
    )
    capa = models.ForeignKey(
        CapaCalendario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tareas',
    )
    completada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', 'prioridad']

    def __str__(self):
        return self.titulo

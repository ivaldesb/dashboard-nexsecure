from django.conf import settings
from django.db import models


class ChecklistTemplate(models.Model):
    nombre = models.CharField(max_length=200)
    tipo_servicio = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.tipo_servicio})'


class ChecklistTemplateItem(models.Model):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    texto = models.CharField(max_length=500)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'pk']

    def __str__(self):
        return self.texto


class VisitaMantenimiento(models.Model):
    PREVENTIVO = 'preventivo'
    CORRECTIVO = 'correctivo'
    TIPO_CHOICES = [
        (PREVENTIVO, 'Preventivo'),
        (CORRECTIVO, 'Correctivo'),
    ]

    PENDIENTE = 'pendiente'
    HECHA = 'hecha'
    CANCELADA = 'cancelada'
    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (HECHA, 'Hecha'),
        (CANCELADA, 'Cancelada'),
    ]

    proyecto = models.ForeignKey(
        'proyectos.Proyecto',
        on_delete=models.CASCADE,
        related_name='visitas_mantenimiento',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=PREVENTIVO)
    tipo_servicio = models.SlugField(max_length=120)
    fecha = models.DateField()
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=PENDIENTE)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='visitas_mantenimiento_creadas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-pk']
        verbose_name = 'visita de mantenimiento'
        verbose_name_plural = 'visitas de mantenimiento'

    def __str__(self):
        return f'{self.proyecto} — {self.get_tipo_display()} ({self.fecha})'


class VisitaChecklistItem(models.Model):
    visita = models.ForeignKey(VisitaMantenimiento, on_delete=models.CASCADE, related_name='checklist')
    texto = models.CharField(max_length=500)
    hecho = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'pk']

    def __str__(self):
        return self.texto


class FotoVisita(models.Model):
    visita = models.ForeignKey(VisitaMantenimiento, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.FileField(upload_to='mantenimiento/fotos/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='fotos_visita_subidas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Foto visita #{self.visita_id}'

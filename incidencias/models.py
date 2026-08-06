from django.conf import settings
from django.db import models


class Incidencia(models.Model):
    ABIERTA = 'abierta'
    EN_PROGRESO = 'en_progreso'
    RESUELTA = 'resuelta'
    CERRADA = 'cerrada'
    ESTADO_CHOICES = [
        (ABIERTA, 'Abierta'),
        (EN_PROGRESO, 'En progreso'),
        (RESUELTA, 'Resuelta'),
        (CERRADA, 'Cerrada'),
    ]

    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='incidencias')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    diagnostico = models.TextField(blank=True)
    causas = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ABIERTA)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='incidencias_creadas',
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incidencias_tecnico',
    )
    activos = models.ManyToManyField('activos.Activo', blank=True, related_name='incidencias')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo


class ComentarioIncidencia(models.Model):
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comentario de {self.autor} en {self.incidencia}'


class FotoIncidencia(models.Model):
    incidencia = models.ForeignKey(Incidencia, on_delete=models.CASCADE, related_name='fotos')
    # ponytail: FileField (no Pillow); upgrade a ImageField si se añade Pillow
    imagen = models.FileField(upload_to='incidencias/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='fotos_incidencia',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Foto {self.pk} — {self.incidencia}'

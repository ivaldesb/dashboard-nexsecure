from django.db import models


class Campana(models.Model):
    """Placeholder reservado para futuras campañas de marketing."""

    nombre = models.CharField(max_length=200)
    activa = models.BooleanField(default=False)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'campaña'
        verbose_name_plural = 'campañas'
        ordering = ['-created_at']

    def __str__(self):
        return self.nombre

from django.conf import settings
from django.db import models
from django.db.models import Max

GENERALIDADES_DEFAULT = (
    'DESPACHO DE PRODUCTOS A LA OBRA\n'
    'INSTALACION DE PRODUCTOS\n'
    'GARANTIA DE 12 MESES A PARTIR DE LA FECHA DE ENTREGA (SUJETO A TERMINOS Y CONDICIONES)\n'
    'TIEMPO DE FABRICACION 4 DIAS.\n'
    'TIEMPO DE EJECUCION 10 DIAS\n'
    'ANTICIPO 50% PARA EL COMIENZO DE LA OBRA - 50% AL FINALIZAR LA OBRA'
)


class EstadoProyecto(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    orden = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=20, default='#0066FF')
    activo = models.BooleanField(default=True)
    visible_cliente = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'estado de proyecto'
        verbose_name_plural = 'estados de proyecto'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Proyecto(models.Model):
    codigo = models.CharField(max_length=32, unique=True, blank=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    generalidades = models.TextField(blank=True, default=GENERALIDADES_DEFAULT)
    progreso = models.PositiveSmallIntegerField(default=0, help_text='0–100')
    estado = models.ForeignKey(EstadoProyecto, on_delete=models.PROTECT, related_name='proyectos')
    clientes = models.ManyToManyField('clientes.Cliente', blank=True, related_name='proyectos')
    equipo = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='proyectos_equipo')
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='proyectos_creados',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'proyecto'
        verbose_name_plural = 'proyectos'
        ordering = ['-updated_at']
        permissions = [('view_all_proyectos', 'Puede ver todos los proyectos')]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not (self.codigo or '').strip():
            # ponytail: next numeric codigo; incluye Nº de ppto para no chocar con adicionales
            max_num = 0
            for c in Proyecto.objects.exclude(codigo='').values_list('codigo', flat=True):
                if c and str(c).isdigit():
                    max_num = max(max_num, int(c))
            max_pk = Proyecto.objects.aggregate(m=Max('pk'))['m'] or 0
            try:
                from presupuestos.models import _max_numero_presupuesto

                max_num = max(max_num, _max_numero_presupuesto())
            except Exception:
                pass
            self.codigo = str(max(max_num, max_pk) + 1)
        super().save(*args, **kwargs)

    def user_has_access(self, user):
        if user.is_system_admin() or user.has_perm('proyectos.view_all_proyectos'):
            return True
        if self.equipo.filter(pk=user.pk).exists():
            return True
        cliente = getattr(user, 'cliente_profile', None)
        if cliente is None or not self.clientes.filter(pk=cliente.pk).exists():
            return False
        return self.estado.visible_cliente


class TimelineEvent(models.Model):
    TIPO_CHOICES = [
        ('estado', 'Cambio de estado'),
        ('documento', 'Documento'),
        ('incidencia', 'Incidencia'),
        ('presupuesto', 'Presupuesto'),
        ('activo', 'Activo'),
        ('otro', 'Otro'),
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='timeline')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    tipo = models.CharField(max_length=32, choices=TIPO_CHOICES, default='otro')
    titulo = models.CharField(max_length=255)
    detalle = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.proyecto} — {self.titulo}'


class ComentarioProyecto(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='comentarios_proyecto',
    )
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'comentario de proyecto'
        verbose_name_plural = 'comentarios de proyecto'

    def __str__(self):
        return f'{self.proyecto} — {self.created_at:%Y-%m-%d %H:%M}'


class TimelineConfig(models.Model):
    proyecto = models.OneToOneField(Proyecto, on_delete=models.CASCADE, related_name='timeline_config')
    auto_estado = models.BooleanField(default=True)
    auto_documento = models.BooleanField(default=True)
    auto_incidencia = models.BooleanField(default=True)
    auto_presupuesto = models.BooleanField(default=True)
    auto_activo = models.BooleanField(default=True)
    visible_cliente_estado = models.BooleanField(default=True)
    visible_cliente_documento = models.BooleanField(default=False)
    visible_cliente_incidencia = models.BooleanField(default=False)
    visible_cliente_presupuesto = models.BooleanField(default=False)
    visible_cliente_activo = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'configuración de timeline'
        verbose_name_plural = 'configuraciones de timeline'

    def __str__(self):
        return f'Timeline — {self.proyecto}'

    def tipos_visibles_cliente(self):
        mapping = [
            ('estado', self.visible_cliente_estado),
            ('documento', self.visible_cliente_documento),
            ('incidencia', self.visible_cliente_incidencia),
            ('presupuesto', self.visible_cliente_presupuesto),
            ('activo', self.visible_cliente_activo),
        ]
        return [tipo for tipo, ok in mapping if ok]


def proyectos_visibles_para(user):
    """Proyectos que el usuario puede ver: admin todo; cliente solo M2M + estado visible; resto equipo."""
    qs = Proyecto.objects.select_related('estado')
    if user.is_system_admin() or user.has_perm('proyectos.view_all_proyectos'):
        return qs
    cliente = getattr(user, 'cliente_profile', None)
    if cliente is not None:
        return qs.filter(clientes=cliente, estado__visible_cliente=True).distinct()
    return qs.filter(equipo=user).distinct()

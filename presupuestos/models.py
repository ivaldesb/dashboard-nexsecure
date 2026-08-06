from decimal import Decimal

from django.conf import settings
from django.db import models

from proyectos.models import GENERALIDADES_DEFAULT

ZERO = Decimal('0')
HUNDRED = Decimal('100')


def _max_numero_presupuesto():
    """Máximo número numérico entre presupuestos (y códigos de proyecto)."""
    max_num = 0
    for n in Presupuesto.objects.exclude(numero='').values_list('numero', flat=True):
        if n and str(n).isdigit():
            max_num = max(max_num, int(n))
    # evitar colisión con códigos de proyecto futuros / existentes
    from proyectos.models import Proyecto

    for c in Proyecto.objects.exclude(codigo='').values_list('codigo', flat=True):
        if c and str(c).isdigit():
            max_num = max(max_num, int(c))
    return max_num


def next_numero_presupuesto():
    return str(_max_numero_presupuesto() + 1)


class Presupuesto(models.Model):
    INICIAL = 'inicial'
    ADICIONAL = 'adicional'
    TIPO_CHOICES = [
        (INICIAL, 'Inicial'),
        (ADICIONAL, 'Adicional'),
    ]

    BORRADOR = 'borrador'
    ENVIADO = 'enviado'
    ACEPTADO = 'aceptado'
    RECHAZADO = 'rechazado'
    ESTADO_CHOICES = [
        (BORRADOR, 'Borrador'),
        (ENVIADO, 'Enviado'),
        (ACEPTADO, 'Aceptado'),
        (RECHAZADO, 'Rechazado'),
    ]

    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='presupuestos')
    numero = models.CharField('Nº presupuesto', max_length=32, unique=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=INICIAL)
    titulo = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=BORRADOR)
    notas = models.TextField(blank=True)
    generalidades = models.TextField(blank=True, default=GENERALIDADES_DEFAULT)
    descuento_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pct_empresa = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    incidencia = models.ForeignKey(
        'incidencias.Incidencia',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='presupuestos',
    )
    # ponytail: mantenimiento may not be in INSTALLED_APPS yet — IntegerField until FK is safe
    visita_mantenimiento_id = models.PositiveIntegerField(null=True, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo', '-created_at']

    def __str__(self):
        return f'#{self.numero or self.pk} — {self.titulo}'

    def assign_numero(self):
        """Inicial = código del proyecto; adicional = último Nº ppto + 1."""
        if (self.numero or '').strip():
            return
        if self.tipo == self.INICIAL and self.proyecto_id:
            codigo = (self.proyecto.codigo or '').strip()
            if codigo and not Presupuesto.objects.filter(numero=codigo).exclude(pk=self.pk).exists():
                self.numero = codigo
                return
        self.numero = next_numero_presupuesto()

    def save(self, *args, **kwargs):
        if not (self.numero or '').strip():
            self.assign_numero()
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return sum((item.subtotal for item in self.items.all()), ZERO)

    def totales_cotizacion(self, iva_rate=None):
        """SUB NETO / descuento / neto / IVA / total (vista cotización)."""
        if iva_rate is None:
            iva_rate = Decimal(str(getattr(settings, 'FINANZAS_IVA_RATE', '0.19')))
        else:
            iva_rate = Decimal(str(iva_rate))
        sub_neto = self.total_items
        desc_pct = self._d_descuento()
        descuento = (sub_neto * desc_pct / HUNDRED).quantize(Decimal('1'))
        neto = sub_neto - descuento
        iva = (neto * iva_rate).quantize(Decimal('1'))
        return {
            'sub_neto': sub_neto.quantize(Decimal('1')),
            'descuento_pct': desc_pct,
            'descuento': descuento,
            'neto': neto.quantize(Decimal('1')),
            'iva_pct': (iva_rate * HUNDRED).quantize(Decimal('1')),
            'iva': iva,
            'total': (neto + iva).quantize(Decimal('1')),
        }

    def _d_descuento(self):
        return self.descuento_pct if self.descuento_pct is not None else ZERO


class PresupuestoItem(models.Model):
    MATERIAL = 'material'
    SERVICIO = 'servicio'
    TIPO_CHOICES = [
        (MATERIAL, 'Material'),
        (SERVICIO, 'Servicio'),
    ]

    PCT_FIELDS = (
        'pct_maquila',
        'pct_instalacion',
        'pct_desinstalacion',
        'pct_ferreteria',
        'pct_flete',
        'pct_gg',
        'pct_utilidad',
    )

    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='items')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=MATERIAL)
    referencia = models.CharField(max_length=255, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    ubicacion = models.CharField(max_length=120, blank=True)
    tipologia = models.CharField('tipología', max_length=120, blank=True)
    caracteristicas = models.CharField('características', max_length=255, blank=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_insumo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pct_maquila = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_instalacion = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_desinstalacion = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_ferreteria = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_flete = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_gg = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    pct_utilidad = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    utilidad_manual = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    neto_unidad = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    incidencia = models.ForeignKey(
        'incidencias.Incidencia',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='presupuesto_items',
    )
    # ponytail: same as Presupuesto — avoid hard FK until mantenimiento is installed
    visita_mantenimiento_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.descripcion or self.referencia or f'Ítem {self.pk}'

    def _d(self, value):
        return value if value is not None else ZERO

    def pct_sum_fraction(self):
        total = sum((self._d(getattr(self, f)) for f in self.PCT_FIELDS), ZERO)
        return total / HUNDRED

    def compute_neto_unidad(self):
        if self.tipo == self.SERVICIO:
            return self._d(self.neto_unidad) or self._d(self.precio_unitario)
        # Neto = CostoInsumo * (1 + sum(pcts)/100); pcts stored as percent numbers (49.2)
        return self._d(self.costo_insumo) * (Decimal('1') + self.pct_sum_fraction())

    def valor_unidad_for(self, pct_field):
        if self.tipo != self.MATERIAL:
            return ZERO
        return self._d(self.costo_insumo) * self._d(getattr(self, pct_field)) / HUNDRED

    @property
    def valor_unidad_maquila(self):
        return self.valor_unidad_for('pct_maquila')

    @property
    def valor_unidad_instalacion(self):
        return self.valor_unidad_for('pct_instalacion')

    @property
    def valor_unidad_desinstalacion(self):
        return self.valor_unidad_for('pct_desinstalacion')

    @property
    def valor_unidad_ferreteria(self):
        return self.valor_unidad_for('pct_ferreteria')

    @property
    def valor_unidad_flete(self):
        return self.valor_unidad_for('pct_flete')

    @property
    def valor_unidad_gg(self):
        return self.valor_unidad_for('pct_gg')

    @property
    def valor_unidad_utilidad(self):
        return self.valor_unidad_for('pct_utilidad')

    @property
    def total_maquila(self):
        return self.valor_unidad_maquila * self._d(self.cantidad)

    @property
    def total_instalacion(self):
        return self.valor_unidad_instalacion * self._d(self.cantidad)

    @property
    def total_desinstalacion(self):
        return self.valor_unidad_desinstalacion * self._d(self.cantidad)

    @property
    def total_ferreteria(self):
        return self.valor_unidad_ferreteria * self._d(self.cantidad)

    @property
    def total_flete(self):
        return self.valor_unidad_flete * self._d(self.cantidad)

    @property
    def total_gg(self):
        return self.valor_unidad_gg * self._d(self.cantidad)

    @property
    def total_utilidad(self):
        return self.valor_unidad_utilidad * self._d(self.cantidad)

    @property
    def subtotal(self):
        neto = self._d(self.neto_unidad) or self._d(self.precio_unitario)
        return self._d(self.cantidad) * neto

    def sync_pricing(self):
        if not self.descripcion and self.referencia:
            self.descripcion = self.referencia
        if self.tipo == self.SERVICIO:
            self.costo_insumo = ZERO
            for f in self.PCT_FIELDS:
                setattr(self, f, ZERO)
            if self.neto_unidad is None:
                self.neto_unidad = self._d(self.precio_unitario)
            self.precio_unitario = self._d(self.neto_unidad)
        else:
            self.neto_unidad = self.compute_neto_unidad().quantize(Decimal('0.01'))
            self.precio_unitario = self.neto_unidad

    def save(self, *args, **kwargs):
        self.sync_pricing()
        super().save(*args, **kwargs)


class FacturaBoleta(models.Model):
    FACTURA = 'factura'
    BOLETA = 'boleta'
    TIPO_CHOICES = [
        (FACTURA, 'Factura'),
        (BOLETA, 'Boleta'),
    ]

    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='facturas')
    presupuesto = models.ForeignKey(
        Presupuesto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='facturas',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=FACTURA)
    numero = models.CharField(max_length=64)
    proveedor = models.CharField(max_length=200, blank=True)
    fecha = models.DateField()
    monto_neto = models.DecimalField(max_digits=14, decimal_places=2)
    monto_iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # null legado; el form exige archivo al crear
    archivo = models.FileField(upload_to='facturas/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} {self.numero}'

    @property
    def total(self):
        return self.monto_neto + self.monto_iva

    def suma_gastos(self, exclude_pk=None):
        qs = self.gastos.all()
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return sum((g.monto for g in qs), ZERO)

    def saldo_disponible(self, exclude_gasto_pk=None):
        return self.total - self.suma_gastos(exclude_pk=exclude_gasto_pk)


class Gasto(models.Model):
    TIPO_MATERIALES = 'materiales'
    TIPO_TRANSPORTE = 'transporte'
    TIPO_MANO_OBRA = 'mano_obra'
    TIPO_OTROS = 'otros'
    TIPO_CHOICES = [
        (TIPO_MATERIALES, 'Materiales'),
        (TIPO_TRANSPORTE, 'Transporte'),
        (TIPO_MANO_OBRA, 'Mano de obra'),
        (TIPO_OTROS, 'Otros'),
    ]

    PAGADO_CAJA = 'caja'
    PAGADO_EMPRESA = 'empresa'
    PAGADO_USUARIO = 'usuario'
    PAGADO_POR_CHOICES = [
        (PAGADO_CAJA, 'Caja del proyecto'),
        (PAGADO_EMPRESA, 'Empresa'),
        (PAGADO_USUARIO, 'Usuario'),
    ]

    proyecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='gastos')
    presupuesto = models.ForeignKey(
        Presupuesto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='gastos',
    )
    # null solo para filas antiguas; el form exige factura al crear
    factura = models.ForeignKey(
        FacturaBoleta,
        null=True,
        blank=False,
        on_delete=models.PROTECT,
        related_name='gastos',
        verbose_name='factura / boleta',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_OTROS)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha = models.DateField()
    pagado_por_tipo = models.CharField(max_length=20, choices=PAGADO_POR_CHOICES, default=PAGADO_CAJA)
    # ponytail: solo relevante si pagado_por_tipo=usuario; views/forms validan
    pagado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='gastos_pagados',
    )
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.descripcion} (${self.monto})'


class PagoEmpleado(models.Model):
    QUIEN_CAJA = 'caja'
    QUIEN_EMPRESA = 'empresa'
    QUIEN_USUARIO = 'usuario'
    QUIEN_CHOICES = [
        (QUIEN_CAJA, 'Caja del proyecto'),
        (QUIEN_EMPRESA, 'Empresa'),
        (QUIEN_USUARIO, 'Usuario'),
    ]

    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='pagos_empleados')
    empleado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pagos_presupuesto',
    )
    porcentaje_pago = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    anticipo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    quien_anticipo_tipo = models.CharField(max_length=20, choices=QUIEN_CHOICES, default=QUIEN_CAJA)
    # ponytail: solo relevante si quien_anticipo_tipo=usuario
    quien_anticipo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='anticipos_pagados',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['empleado_id']
        unique_together = [('presupuesto', 'empleado')]

    def __str__(self):
        return f'{self.empleado} — {self.porcentaje_pago}%'

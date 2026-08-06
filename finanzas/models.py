from django.conf import settings
from django.db import models


class DocumentoSII(models.Model):
    periodo = models.DateField(help_text='Usar el día 1 del mes del período.')
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='sii/')
    notas = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'documento SII'
        verbose_name_plural = 'documentos SII'
        ordering = ['-periodo', '-created_at']

    def __str__(self):
        return f'{self.titulo} ({self.periodo:%Y-%m})'


class CuentaBancaria(models.Model):
    nombre = models.CharField(max_length=120)
    banco = models.CharField(max_length=120)
    numero = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = 'cuenta bancaria'
        verbose_name_plural = 'cuentas bancarias'
        ordering = ['nombre']

    def __str__(self):
        if self.numero:
            return f'{self.nombre} — {self.banco} ({self.numero})'
        return f'{self.nombre} — {self.banco}'


class MovimientoCuenta(models.Model):
    CARGO = 'cargo'
    ABONO = 'abono'
    TIPO_CHOICES = [
        (CARGO, 'Cargo'),
        (ABONO, 'Abono'),
    ]

    fecha = models.DateField()
    cuenta = models.CharField(max_length=120, default='principal')
    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='movimientos',
    )
    factura = models.ForeignKey(
        'presupuestos.FacturaBoleta',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='movimientos',
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True)
    referencia = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f'{self.fecha} {self.get_tipo_display()} ${self.monto}'


class PeriodoTributario(models.Model):
    periodo = models.DateField(unique=True, help_text='Día 1 del mes.')
    total_neto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva_debito = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva_credito = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva_a_pagar = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ppm = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'período tributario'
        verbose_name_plural = 'períodos tributarios'
        ordering = ['-periodo']

    def __str__(self):
        return f'Período {self.periodo:%Y-%m}'

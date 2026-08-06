from django.contrib import admin

from finanzas.models import CuentaBancaria, DocumentoSII, MovimientoCuenta, PeriodoTributario


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'banco', 'numero')
    search_fields = ('nombre', 'banco', 'numero')


@admin.register(DocumentoSII)
class DocumentoSIIAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'periodo', 'uploaded_by', 'created_at')
    list_filter = ('periodo',)


@admin.register(MovimientoCuenta)
class MovimientoCuentaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'monto', 'cuenta', 'cuenta_bancaria', 'factura')
    list_filter = ('tipo', 'cuenta')
    search_fields = ('descripcion', 'referencia', 'cuenta')


@admin.register(PeriodoTributario)
class PeriodoTributarioAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'total_neto', 'iva_debito', 'iva_credito', 'iva_a_pagar', 'ppm')

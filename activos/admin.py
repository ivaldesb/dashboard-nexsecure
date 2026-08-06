from django.contrib import admin

from activos.models import Activo, CategoriaActivo


@admin.register(CategoriaActivo)
class CategoriaActivoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proyecto', 'categoria', 'ubicacion', 'ip_dominio', 'factura', 'tecnico', 'updated_at')
    list_filter = ('categoria', 'proyecto')
    search_fields = ('nombre', 'sn', 'ip_dominio', 'ubicacion')
    raw_id_fields = ('proyecto', 'tecnico', 'factura')
    autocomplete_fields = ('categoria',)

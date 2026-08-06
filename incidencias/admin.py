from django.contrib import admin

from incidencias.models import ComentarioIncidencia, FotoIncidencia, Incidencia


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proyecto', 'estado', 'autor', 'tecnico', 'created_at')
    list_filter = ('estado',)
    filter_horizontal = ('activos',)


admin.site.register(ComentarioIncidencia)
admin.site.register(FotoIncidencia)

from django.contrib import admin

from proyectos.models import ComentarioProyecto, EstadoProyecto, Proyecto, TimelineConfig, TimelineEvent


@admin.register(EstadoProyecto)
class EstadoProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'orden', 'visible_cliente', 'activo')
    list_filter = ('visible_cliente', 'activo')
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    search_fields = ('nombre', 'codigo')
    list_display = ('nombre', 'codigo', 'estado', 'updated_at')


admin.site.register(TimelineEvent)
admin.site.register(ComentarioProyecto)
admin.site.register(TimelineConfig)

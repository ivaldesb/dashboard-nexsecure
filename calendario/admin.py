from django.contrib import admin

from calendario.models import CapaCalendario, Evento, Tarea


@admin.register(CapaCalendario)
class CapaCalendarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'user', 'color', 'visible')
    list_filter = ('visible',)
    search_fields = ('nombre', 'user__username')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'inicio', 'fin', 'creador', 'capa')
    list_filter = ('tipo',)
    search_fields = ('titulo', 'ubicacion')
    filter_horizontal = ('asignados',)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'prioridad', 'deadline', 'completada', 'creador', 'capa')
    list_filter = ('prioridad', 'completada')
    search_fields = ('titulo',)
    filter_horizontal = ('asignados',)

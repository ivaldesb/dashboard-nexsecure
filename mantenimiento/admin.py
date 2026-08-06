from django.contrib import admin

from mantenimiento.models import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    FotoVisita,
    VisitaChecklistItem,
    VisitaMantenimiento,
)


class ChecklistTemplateItemInline(admin.TabularInline):
    model = ChecklistTemplateItem
    extra = 1


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_servicio')
    search_fields = ('nombre', 'tipo_servicio')
    prepopulated_fields = {'tipo_servicio': ('nombre',)}
    inlines = [ChecklistTemplateItemInline]


class VisitaChecklistItemInline(admin.TabularInline):
    model = VisitaChecklistItem
    extra = 0


class FotoVisitaInline(admin.TabularInline):
    model = FotoVisita
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(VisitaMantenimiento)
class VisitaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'tipo', 'tipo_servicio', 'fecha', 'estado', 'creado_por')
    list_filter = ('tipo', 'estado', 'tipo_servicio')
    search_fields = ('proyecto__nombre', 'observaciones')
    date_hierarchy = 'fecha'
    inlines = [VisitaChecklistItemInline, FotoVisitaInline]


@admin.register(FotoVisita)
class FotoVisitaAdmin(admin.ModelAdmin):
    list_display = ('visita', 'uploaded_by', 'created_at')
    readonly_fields = ('created_at',)

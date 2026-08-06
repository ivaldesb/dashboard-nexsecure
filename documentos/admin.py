from django.contrib import admin

from documentos.models import CategoriaDocumento, Documento, DocumentoAudit


@admin.register(CategoriaDocumento)
class CategoriaDocumentoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proyecto', 'categoria', 'visible_cliente', 'solo_admin', 'uploaded_by', 'created_at')
    list_filter = ('solo_admin', 'visible_cliente', 'categoria')
    search_fields = ('titulo',)
    filter_horizontal = ('users_allowed',)


@admin.register(DocumentoAudit)
class DocumentoAuditAdmin(admin.ModelAdmin):
    list_display = ('documento', 'user', 'action', 'created_at')
    list_filter = ('action',)

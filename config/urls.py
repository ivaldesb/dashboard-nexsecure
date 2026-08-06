from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('clientes/', include('clientes.urls')),
    path('proyectos/', include('proyectos.urls')),
    path('activos/', include('activos.urls')),
    path('documentos/', include('documentos.urls')),
    path('incidencias/', include('incidencias.urls')),
    path('presupuestos/', include('presupuestos.urls')),
    path('finanzas/', include('finanzas.urls')),
    path('calendario/', include('calendario.urls')),
    path('marketing/', include('marketing.urls')),
    path('mantenimiento/', include('mantenimiento.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

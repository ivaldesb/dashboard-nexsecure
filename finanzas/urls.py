from django.urls import path

from finanzas import views

app_name = 'finanzas'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('periodos/', views.periodos_list, name='periodos_list'),
    path('periodos/<int:year>/<int:month>/recalcular/', views.recalcular_periodo, name='recalcular_periodo'),
    path('sii/', views.documentos_sii, name='sii_list'),
    path('sii/nuevo/', views.documento_sii_upload, name='sii_upload'),
    path('sii/<int:pk>/eliminar/', views.documento_sii_delete, name='sii_delete'),
    path('movimientos/', views.movimientos_list, name='movimientos_list'),
    path('movimientos/nuevo/', views.movimiento_create, name='movimiento_create'),
    path('movimientos/importar/', views.movimientos_import, name='movimientos_import'),
]

from django.urls import path

from presupuestos import views

app_name = 'presupuestos'

urlpatterns = [
    path('proyecto/<int:proyecto_id>/adicional/', views.create_adicional, name='create_adicional'),
    path('proyecto/<int:proyecto_id>/gasto/', views.gasto_add, name='gasto_add'),
    path('proyecto/<int:proyecto_id>/factura/', views.factura_add, name='factura_add'),
    path('items/<int:pk>/editar/', views.item_edit, name='item_edit'),
    path('items/<int:pk>/eliminar/', views.item_delete, name='item_delete'),
    path('<int:presupuesto_id>/items/nuevo/', views.item_add, name='item_add'),
    path('<int:pk>/pdf/', views.pdf_presupuesto, name='pdf_presupuesto'),
    path('<int:pk>/enviar/', views.enviar, name='enviar'),
    path('<int:pk>/aceptar/', views.aceptar, name='aceptar'),
    path('<int:pk>/rechazar/', views.rechazar, name='rechazar'),
    path('<int:presupuesto_id>/', views.detail, name='detail'),
]

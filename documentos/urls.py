from django.urls import path

from documentos import views

app_name = 'documentos'

urlpatterns = [
    path('subir/<int:proyecto_id>/', views.upload, name='upload'),
    path('<int:pk>/ver/', views.view_doc, name='view'),
    path('<int:pk>/descargar/', views.download, name='download'),
    path('<int:pk>/acl/', views.edit_acl, name='edit_acl'),
    path('<int:pk>/eliminar/', views.delete, name='delete'),
]

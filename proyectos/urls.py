from django.urls import path

from proyectos import views

app_name = 'proyectos'

urlpatterns = [
    path('', views.list, name='list'),
    path('nuevo/', views.create, name='create'),
    path('estados/', views.estado_list, name='estado_list'),
    path('estados/nuevo/', views.estado_create, name='estado_create'),
    path('estados/<int:pk>/editar/', views.estado_edit, name='estado_edit'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/editar/', views.edit, name='edit'),
    path('<int:pk>/eliminar/', views.delete, name='delete'),
    path('<int:pk>/estado/', views.change_estado, name='change_estado'),
    path('<int:pk>/comentario/', views.add_comentario, name='add_comentario'),
    path('<int:pk>/generalidades/', views.save_generalidades, name='save_generalidades'),
    path('<int:pk>/timeline-config/', views.timeline_config, name='timeline_config'),
    path('<int:pk>/pdf/', views.pdf_reporte, name='pdf_reporte'),
]

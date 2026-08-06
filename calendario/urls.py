from django.urls import path

from calendario import views

app_name = 'calendario'

urlpatterns = [
    path('', views.list_eventos, name='list'),
    path('nuevo/', views.create, name='create'),
    path('tareas/', views.list_tareas, name='tareas'),
    path('tareas/nueva/', views.create_tarea, name='tarea_create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/editar/', views.edit, name='edit'),
]

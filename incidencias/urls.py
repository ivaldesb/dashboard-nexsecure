from django.urls import path

from incidencias import views

app_name = 'incidencias'

urlpatterns = [
    path('', views.list_incidencias, name='list'),
    path('proyecto/<int:proyecto_id>/nueva/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/estado/', views.update_estado, name='update_estado'),
    path('<int:pk>/comentario/', views.add_comentario, name='add_comentario'),
    path('<int:pk>/foto/', views.add_foto, name='add_foto'),
]

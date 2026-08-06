from django.urls import path

from activos import views

app_name = 'activos'

urlpatterns = [
    path('', views.list_activos, name='list'),
    path('nuevo/', views.create, name='create'),
    path('<int:pk>/editar/', views.edit, name='edit'),
    path('<int:pk>/eliminar/', views.delete, name='delete'),
]

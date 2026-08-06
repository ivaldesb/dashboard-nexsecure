from django.urls import path

from mantenimiento import views

app_name = 'mantenimiento'

urlpatterns = [
    path('proyecto/<int:proyecto_id>/', views.list_visitas, name='list'),
    path('proyecto/<int:proyecto_id>/nueva/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/checklist/<int:item_id>/toggle/', views.toggle_checklist, name='toggle_checklist'),
    path('<int:pk>/foto/', views.upload_foto, name='upload_foto'),
]

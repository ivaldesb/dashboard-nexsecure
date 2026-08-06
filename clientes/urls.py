from django.urls import path

from clientes import views

app_name = 'clientes'

urlpatterns = [
    path('', views.list, name='list'),
    path('portal/', views.portal, name='portal'),
    path('nuevo/', views.create, name='create'),
    path('<int:pk>/editar/', views.edit, name='edit'),
    path('<int:pk>/toggle/', views.toggle, name='toggle'),
]

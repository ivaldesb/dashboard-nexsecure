from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('users/nuevo/', views.user_create, name='user_create'),
    path('users/<int:pk>/editar/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/nuevo/', views.role_create, name='role_create'),
    path('roles/<int:pk>/editar/', views.role_edit, name='role_edit'),
    path('roles/<int:pk>/eliminar/', views.role_delete, name='role_delete'),
]

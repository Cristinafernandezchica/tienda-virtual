from django.urls import path
from django.contrib.auth import views as auth_views

from usuarios.forms import CustomAuthenticationForm
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('register/', views.register, name='register'),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='usuarios/login.html',
            authentication_form=CustomAuthenticationForm
        ),
        name='login'
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('datos-entrega/', views.datos_entrega, name='datos_entrega'),
    path('datos-entrega/add-direccion/', views.add_direccion, name='add_direccion'),
    path('direccion/<int:id>/editar/', views.editar_direccion, name='editar_direccion'),
    path('direccion/<int:id>/eliminar/', views.eliminar_direccion, name='eliminar_direccion'),
    path('direccion/<int:id>/preferida/', views.preferida_direccion, name='preferida_direccion'),
    path('puntos-recogida/', views.datos_puntos, name='gestion_puntos'),
    path('puntos-recogida/add-punto/', views.add_punto_recogida, name='add_punto'),
    path('puntos-recogida/<int:id>/editar/', views.editar_punto, name='editar_punto'),
    path('puntos-recogida/<int:id>/eliminar/', views.eliminar_punto, name='eliminar_punto'),  
    path('punto/<int:id>/preferido/', views.preferido_punto, name='preferido_punto'),


    # Administración: Lista de clientes registrados
    path('clientes-registrados/', views.lista_clientes, name='lista_clientes'),
]
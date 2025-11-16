from django.shortcuts import render
from django.urls import path
from . import views


urlpatterns = [
    path("", views.ver_cesta, name='ver_cesta'),
    path('cesta/añadir/<int:producto_id>/', views.añadir_a_cesta, name='añadir_a_cesta'),
    path("eliminar/<int:producto_id>/", views.eliminar_de_cesta, name='eliminar_de_cesta'),
    path("añadir_producto/<int:producto_id>/<int:cantidad>/", views.añadir_producto_a_cesta, name='añadir_producto_a_cesta'),
    path("quitar_producto/<int:producto_id>/", views.quitar_producto_de_cesta, name='quitar_1de_cesta'),
    path("checkout/", views.checkout_view, name='checkout'),
    path("pago_simulacion/<int:pedido_id>/", views.pago_externo_simulacion, name='pago_externo_simulacion'),
    path("pedido_confirmacion/<int:pedido_id>/", views.pedido_confirmacion, name='pedido_confirmacion'),
    path("mis_pedidos/", views.mis_pedidos, name='mis_pedidos'),
    path("pedido_admin/<int:pedido_id>/", views.pedido_admin_detalle, name="pedido_admin_detalle"),
    path("pedidos_admin/", views.lista_pedidos_admin, name="lista_pedidos_admin"),
    
    # NUEVAS RUTAS DE STRIPE:
    path("stripe_checkout/<int:pedido_id>/", views.stripe_checkout, name='stripe_checkout'),  # Inicia la sesión de Stripe
    path("pago_exito/<int:pedido_id>/", views.pago_exito, name='pago_exito'),  # Retorno exitoso
    path("pago_fallo/<int:pedido_id>/", views.pago_fallo, name='pago_fallo'),  # Retorno fallido/cancelado
       
]

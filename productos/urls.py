from django.urls import path
from . import views

app_name = 'productos' 

urlpatterns = [
    # --- Cliente ---
    path('producto/<int:producto_id>/', views.ficha_producto, name='ficha_producto'),
    
    # --- Administrador ---

    path('gestionProducts/', views.ProductoListView.as_view(), name='gestion_productos'),
    
    path('gestionProducts/producto/crear/', views.ProductoCreateView.as_view(), name='producto_crear'),
    path('gestionProducts/producto/editar/<int:pk>/', views.ProductoUpdateView.as_view(), name='producto_editar'),
    path('gestionProducts/producto/eliminar/<int:pk>/', views.ProductoDeleteView.as_view(), name='producto_eliminar'),
    path('gestion_ventas/', views.gestion_ventas, name='gestion_ventas'),
]
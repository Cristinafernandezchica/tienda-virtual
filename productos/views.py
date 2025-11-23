from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    CreateView, UpdateView, DeleteView, ListView
)
from .models import Producto, Categoria
from .forms import ProductoForm 
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.contrib import messages
from cesta.models import Pedido, Cesta, EstadoCesta
from django.db import transaction
from django.db.models import Q # Importado para consultas OR


# --- MIXINS Y DECORADORES ---

def admin_required_view(func):
    """Decorator helper that checks usuario rol ADMIN or superuser."""
    return user_passes_test(lambda u: (hasattr(u, 'rol') and u.rol == 'ADMIN') or u.is_superuser, login_url=reverse_lazy('usuarios:login'))(func)

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Asegura que el usuario esté logueado y tenga el rol de Administrador.
    """
    def test_func(self):
        # El usuario es administrador si su campo 'rol' es 'ADMIN' O si es un superusuario.
        is_admin_rol = hasattr(self.request.user, 'rol') and self.request.user.rol == 'ADMIN'
        return is_admin_rol 
    
    permission_denied_message = "Debes ser administrador para acceder a esta página."
    login_url = reverse_lazy('usuarios:login') 


# --- VISTAS DE PRODUCTOS ---

@admin_required_view
def gestion_ventas(request):
    """Pantalla de gestión de ventas: lista productos con unidades vendidas y permite búsqueda/filtrado."""
    
    productos = Producto.objects.all()
    get_params = request.GET
    
    query = get_params.get('q')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(categoria__nombre__icontains=query) 
        )

    categoria_id = get_params.get('categoria')
    if categoria_id:
        try:
            productos = productos.filter(categoria_id=int(categoria_id))
        except ValueError:
            pass 

    orden = get_params.get('orden')
    if orden == 'nombre_asc':
        productos = productos.order_by('nombre')
    elif orden == 'nombre_desc':
        productos = productos.order_by('-nombre')
    elif orden == 'vendidos_asc':
        productos = productos.order_by('vendidos', 'nombre')
    elif orden == 'vendidos_desc' or not orden:
        productos = productos.order_by('-vendidos', 'nombre')
    
    context = {
        'productos': productos,
        'categorias': Categoria.objects.all().order_by('nombre'), 
        'query': query, 
        'categoria_seleccionada': categoria_id, 
        'orden_seleccionado': orden, 
    }
    return render(request, 'productos/gestion_ventas.html', context)

def ficha_producto(request, producto_id):
    """Muestra la ficha detallada de un producto."""
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'productos/ficha_producto.html', {'producto': producto})


# --- VISTAS BASADAS EN CLASES (ADMIN) ---

class ProductoListView(AdminRequiredMixin, ListView):
    """Lista de productos para la gestión interna con funcionalidad de búsqueda, filtro y ordenamiento."""
    model = Producto
    template_name = 'productos/gestion_productos.html'
    context_object_name = 'productos'
    
    # Eliminamos 'ordering' aquí, ya que lo gestionaremos en get_queryset

    def get_queryset(self):
        """
        Sobrescribe para aplicar la lógica de búsqueda, filtro por categoría y ordenamiento.
        """
        queryset = super().get_queryset()
        get_params = self.request.GET
        
        # 1. Búsqueda por texto (q)
        query = get_params.get('q')
        if query:
            # Filtra por nombre, descripción o nombre de categoría (usando __icontains para ser insensible a mayúsculas/minúsculas)
            queryset = queryset.filter(
                Q(nombre__icontains=query) | 
                Q(descripcion__icontains=query) |
                Q(categoria__nombre__icontains=query) 
            )

        # 2. Filtrado por Categoría
        categoria_id = get_params.get('categoria')
        if categoria_id:
            try:
                # Si el ID es válido, filtramos por la categoría
                queryset = queryset.filter(categoria_id=int(categoria_id))
            except ValueError:
                # Ignoramos si el ID de categoría no es un número válido
                pass

        # 3. Ordenamiento
        orden = get_params.get('orden')
        if orden:
            if orden == 'nombre_asc':
                queryset = queryset.order_by('nombre')
            elif orden == 'nombre_desc':
                queryset = queryset.order_by('-nombre')
            elif orden == 'stock_asc':
                queryset = queryset.order_by('stock')
            elif orden == 'stock_desc':
                queryset = queryset.order_by('-stock')
        else:
            # Orden por defecto: nombre ascendente
            queryset = queryset.order_by('nombre')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Sobrescribe para pasar categorías, el término de búsqueda y los filtros seleccionados 
        a la plantilla para mantener el estado.
        """
        context = super().get_context_data(**kwargs)
        get_params = self.request.GET
        
        # Pasamos todas las categorías para el select/dropdown
        context['categorias'] = Categoria.objects.all().order_by('nombre')
        
        # Pasar los valores seleccionados para mantener el estado del formulario
        context['query'] = get_params.get('q', None) 
        context['categoria_seleccionada'] = get_params.get('categoria', None)
        context['orden_seleccionado'] = get_params.get('orden', None)
        
        return context


class ProductoCreateView(AdminRequiredMixin, CreateView):
    """Crea un nuevo producto."""
    model = Producto
    form_class = ProductoForm 
    template_name = 'productos/producto_formulario.html'
    success_url = reverse_lazy('productos:gestion_productos') 

class ProductoUpdateView(AdminRequiredMixin, UpdateView):
    """Edita un producto existente."""
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/producto_formulario.html'
    success_url = reverse_lazy('productos:gestion_productos')

class ProductoDeleteView(AdminRequiredMixin, DeleteView):
    """Elimina un producto (con lógica condicional)."""
    model = Producto
    template_name = 'productos/producto_confirm_delete.html'
    success_url = reverse_lazy('productos:gestion_productos')
    context_object_name = 'producto'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        producto = self.object
        
        # Importación local para evitar la dependencia circular al inicio del módulo
        from cesta.models import Pedido, Cesta, EstadoCesta
        from .models import ProductoCesta 

        # 1. Comprobar si el producto está en algún Pedido (Cesta FINALIZADA asociada a Pedido)
        en_pedido = Pedido.objects.filter(cesta_asociada__producto_cestas__producto=producto).exists()

        if en_pedido:
            # No se elimina el producto -> solo stock a 0
            producto.stock = 0
            producto.save()
            
            # Buscar cestas abiertas (activas) que contengan el producto para limpiarlas
            cestas_activas = Cesta.objects.filter(producto_cestas__producto=producto,estadoCesta=EstadoCesta.ABIERTA).distinct()

            if cestas_activas.exists():
                with transaction.atomic():
                    # Eliminar el producto solo de cestas activas
                    for cesta in cestas_activas:
                        # Asume que tu modelo Cesta tiene un método 'eliminar_producto'
                        cesta.eliminar_producto(producto) 

            messages.success(
                request,
                f"El producto '{producto.nombre}' aparece en pedidos finalizados. "
                "No se elimina del sistema, pero su stock ha sido puesto a 0."
            )
            return redirect(self.success_url)

        # 2. ¿Está en alguna cesta activa?
        cestas_activas = Cesta.objects.filter(producto_cestas__producto=producto,estadoCesta=EstadoCesta.ABIERTA).distinct()

        if cestas_activas.exists():
            with transaction.atomic():
                # Eliminar el producto solo de cestas activas
                for cesta in cestas_activas:
                    cesta.eliminar_producto(producto)

                # Guardar nombre para el mensaje
                producto_nombre = producto.nombre

                # Eliminar el producto del sistema
                self.object.delete()

            messages.success(
                request,
                f"El producto '{producto_nombre}' ha sido eliminado del sistema."
            )
            return redirect(self.success_url)

        # 3. Opción por defecto: No está en Pedidos ni Cestas -> Eliminar directamente
        else:
            producto_nombre = producto.nombre
            self.object.delete()
            messages.success(
                request, 
                f"El producto '{producto_nombre}' ha sido eliminado del sistema."
            )
            return redirect(self.success_url)
from django.shortcuts import render, get_object_or_404 
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    CreateView, UpdateView, DeleteView, ListView
)
from .models import Producto, Categoria
from .forms import ProductoForm 
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy


def admin_required_view(func):
    """Decorator helper that checks usuario rol ADMIN or superuser."""
    return user_passes_test(lambda u: (hasattr(u, 'rol') and u.rol == 'ADMIN') or u.is_superuser, login_url=reverse_lazy('usuarios:login'))(func)


@admin_required_view
def gestion_ventas(request):
    """Pantalla de gestión de ventas: lista productos con stock>0 y unidades vendidas."""
    productos = Producto.objects.filter(stock__gt=0).order_by('-vendidos', 'nombre')
    return render(request, 'productos/gestion_ventas.html', {'productos': productos})

def ficha_producto(request, producto_id):
    """Muestra la ficha detallada de un producto."""
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'productos/ficha_producto.html', {'producto': producto})

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



class ProductoListView(AdminRequiredMixin, ListView):
    """Lista de productos para la gestión interna."""
    model = Producto
    template_name = 'productos/gestion_productos.html'
    context_object_name = 'productos'
    ordering = ['nombre'] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all().order_by('nombre')
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
    """Elimina un producto."""
    model = Producto
    template_name = 'productos/producto_confirm_delete.html'
    success_url = reverse_lazy('productos:gestion_productos')
    context_object_name = 'producto'

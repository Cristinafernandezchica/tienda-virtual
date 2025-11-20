from django.shortcuts import render, redirect
from django.db.models import Q 
from django.contrib import messages

# CRUCIAL: Importamos los modelos Producto y Categoria
from productos.models import Producto, Categoria 

# --- VISTA PRINCIPAL (index) ---
def index(request):
    """Muestra los productos más vendidos en la página principal."""
    productos_top = Producto.objects.order_by('-vendidos')[:10]
    contexto = {
        'productos_top': productos_top
    }
    return render(request, 'index.html', contexto)

# --- VISTA DE CATÁLOGO (CON FILTROS Y ORDENACIÓN) ---
def catalogo(request):
    """Muestra el catálogo con lógica de búsqueda, categoría, precio y ordenación."""
    
    query = request.GET.get('q') 
    categoria_id = request.GET.get('categoria') 
    orden = request.GET.get('orden', '') 
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')

    productos = Producto.objects.all()
    
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)

    if precio_min:
        try:
            productos = productos.filter(precio__gte=float(precio_min))
        except ValueError:
            pass 

    if precio_max:
        try:
            productos = productos.filter(precio__lte=float(precio_max))
        except ValueError:
            pass

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        ).distinct()
    
    if orden == 'precio_asc':
        productos = productos.order_by('precio') 
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio') 
    elif orden == 'nombre_asc':
        productos = productos.order_by('nombre')
    elif orden == 'nombre_desc':
        productos = productos.order_by('-nombre')
    
    categorias = Categoria.objects.all().order_by('nombre')
        
    contexto = {
        'productos': productos,
        'query': query,
        'categorias': categorias, # <-- La variable 'categorias' ya está definida.
        'categoria_seleccionada': categoria_id,
        'orden_seleccionado': orden,
        'precio_min': precio_min,
        'precio_max': precio_max,
    }
    
    return render(request, 'catalogo.html', contexto)


def company_info(request):
    """Muestra la información de contacto global de la empresa.

    Se busca la instancia de `ContactInfo` con `active=True`. Si no existe,
    se toma la última creada. Si tampoco hay, la plantilla mostrará un mensaje
    por defecto.
    """
    from .models import ContactInfo
    from .forms import ContactInfoForm

    contact = ContactInfo.objects.filter(active=True).order_by('-updated_at').first()
    if not contact:
        contact = ContactInfo.objects.order_by('-updated_at').first()

    # Si se recibe un POST y el usuario es admin, procesar el formulario
    if request.method == 'POST':
        # Solo admins permiten crear/editar desde esta vista
        if not (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'rol', '') == 'ADMIN')):
            messages.error(request, 'No estás autorizado para modificar la información de contacto.')
            return redirect('company_info')

        if contact:
            form = ContactInfoForm(request.POST, instance=contact)
        else:
            form = ContactInfoForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            # Al guardar desde esta vista, marcar como activo y desactivar otros
            obj.active = True
            obj.save()
            ContactInfo.objects.exclude(pk=obj.pk).update(active=False)
            messages.success(request, 'Información de contacto actualizada correctamente.')
            return redirect('company_info')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')

    else:
        form = ContactInfoForm(instance=contact) if (request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'rol', '') == 'ADMIN')) else None

    return render(request, 'company_info.html', {'contact_info': contact, 'form': form})
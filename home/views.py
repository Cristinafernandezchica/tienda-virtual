from django.shortcuts import render
from django.db.models import Q 

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
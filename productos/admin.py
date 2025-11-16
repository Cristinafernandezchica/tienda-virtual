from django.contrib import admin
from .models import Producto, Categoria, ProductoCesta

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    fields = ('nombre', 'descripcion', 'imagen')
    list_display = ('nombre', 'descripcion')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 
        'precio', 
        'categoria', 
        'stock', 
        'vendidos', 
        'fabricante',
        'imagen'
    )
    
    fields = (
        'nombre', 
        'precio', 
        'categoria', 
        'stock', 
        'descripcion', 
        'vendidos', 
        'imagen', 
        'fabricante'
    )
    
    list_filter = ('categoria', 'fabricante')
    search_fields = ('nombre', 'descripcion', 'fabricante')

@admin.register(ProductoCesta)
class ProductoCestaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad', 'subtotal')
    search_fields = ('producto__nombre',)
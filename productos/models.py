from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField()
    descripcion = models.TextField()
    vendidos = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    fabricante = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class ProductoCesta(models.Model):
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    # Referencia a la cesta que contiene este elemento. Usamos una cadena para evitar
    # importaciones circulares entre las apps `productos` y `cesta`.
    cesta = models.ForeignKey('cesta.Cesta', on_delete=models.CASCADE, related_name='producto_cestas', null=True, blank=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto} (Subtotal: {self.subtotal})"
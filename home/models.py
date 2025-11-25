from django.db import models

# Create your models here.


class Producto(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Escaparate(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.producto.id)


class ContactInfo(models.Model):
    """Información de contacto pública de la empresa.

    Modelo sencillo sin relaciones. Los administradores pueden editarlo
    desde el admin de Django; la vista pública mostrará la instancia marcada
    como `active=True` o la última creada si no hay ninguna activa.
    """

    nombre = models.CharField(max_length=200, default="Tractor Amarillo")
    descripcion = models.TextField(blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    telefono = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    active = models.BooleanField(
        default=False, help_text="Marcar como activo para mostrar en la web"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.nombre} ({'activo' if self.active else 'inactivo'})"

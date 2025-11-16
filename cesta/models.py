from django.db import models, transaction
from decimal import Decimal
from productos.models import ProductoCesta
from usuarios.models import PuntoRecogidaPref, Usuario
from django.utils.translation import gettext_lazy as _

class EstadoCesta(models.TextChoices):
    """Estados posibles para una Cesta."""
    ABIERTA = 'Activa', _('Activa')
    FINALIZADA = 'Finalizada', _('Finalizada')

class EstadoPedido(models.TextChoices):
    """Estados posibles para un Pedido."""
    PENDIENTE = 'Pendiente', _('Pendiente') 
    EN_PREPARACION = 'EnPreparacion', _('En Preparación')
    EN_ENVIO = 'EnEnvio', _('En Envío')
    ENTREGADO = 'Entregado', _('Entregado')

class EstadoPago(models.TextChoices):
    """Estados posibles para el Pago."""
    PENDIENTE = 'Pendiente', _('Pendiente')
    COMPLETADO = 'Completado', _('Completado')

class TipoEntrega(models.TextChoices):
    """Tipos de entrega disponibles."""
    DOMICILIO = 'Domicilio', _('Domicilio')
    PUNTO_RECOGIDA = 'PuntoRecogida', _('Punto Recogida')

class MetodoPago(models.TextChoices):
    """Métodos de pago disponibles."""
    TARJETA = 'TAR', _('Tarjeta')
    CONTRAREEMBOLSO = 'CRD', _('Contrareembolso')

class Cesta(models.Model):
    # Relación ManyToMany con Producto a través del modelo intermedio ProductoCesta.
    # Usamos referencias en forma de cadena para evitar importaciones circulares entre apps.
    productos = models.ManyToManyField('productos.Producto', through='productos.ProductoCesta', related_name='cestas')
    importeTotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estadoCesta = models.CharField(max_length=20, choices=EstadoCesta.choices, default=EstadoCesta.ABIERTA)
    usuario = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cestaDeCompra' 
    )

    def __str__(self):
        return f"Cesta {self.id} - Estado: {self.estadoCesta} - Importe Total: {self.importeTotal}"

    def añadir_producto(self, producto, cantidad=1):
        """
        Añade `cantidad` unidades de `producto` a esta cesta.

        `producto` puede ser una instancia de `productos.models.Producto` o su id (int).
        Devuelve la instancia de `productos.models.ProductoCesta` creada o actualizada.

        Comportamiento:
        - Si ya existe un ProductoCesta para (cesta, producto), incrementa la cantidad y actualiza el subtotal.
        - Si no existe, crea un nuevo ProductoCesta con el subtotal calculado.
        - Recalcula y guarda `importeTotal` sumando los subtotales de los elementos de la cesta.

        Lanza ValueError si `cantidad` <= 0.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        # Importar localmente para evitar dependencias circulares en importación de módulos
        from productos.models import Producto, ProductoCesta
        # Resolver si nos pasan un id
        if isinstance(producto, int):
            producto = Producto.objects.get(pk=producto)

        with transaction.atomic():
            pc_qs = ProductoCesta.objects.select_for_update().filter(cesta=self, producto=producto)
            if pc_qs.exists():
                pc = pc_qs.first()
                pc.cantidad = pc.cantidad + cantidad
                pc.subtotal = (Decimal(pc.cantidad) * producto.precio).quantize(Decimal('0.01'))
                pc.save()
            else:
                subtotal = (Decimal(cantidad) * producto.precio).quantize(Decimal('0.01'))
                pc = ProductoCesta.objects.create(cesta=self, producto=producto, cantidad=cantidad, subtotal=subtotal)

            # Recalcular importeTotal sumando subtotales
            total = ProductoCesta.objects.filter(cesta=self).aggregate(models.Sum('subtotal'))['subtotal__sum'] or Decimal('0.00')
            # Asegurar Decimal
            if not isinstance(total, Decimal):
                total = Decimal(str(total))
            self.importeTotal = total
            self.save()

        return pc
    
    def eliminar_producto(self, producto):
        """
        Elimina `producto` de esta cesta.

        `producto` puede ser una instancia de `productos.models.Producto` o su id (int).

        Comportamiento:
        - Si existe un ProductoCesta para (cesta, producto), lo elimina.
        - Recalcula y guarda `importeTotal` sumando los subtotales restantes.

        No hace nada si el producto no está en la cesta.
        """
        # Importar localmente para evitar dependencias circulares en importación de módulos
        from productos.models import Producto, ProductoCesta
        # Resolver si nos pasan un id
        if isinstance(producto, int):
            producto = Producto.objects.get(pk=producto)

        with transaction.atomic():
            pc_qs = ProductoCesta.objects.select_for_update().filter(cesta=self, producto=producto)
            if pc_qs.exists():
                pc_qs.delete()

                # Recalcular importeTotal sumando subtotales restantes
                total = ProductoCesta.objects.filter(cesta=self).aggregate(models.Sum('subtotal'))['subtotal__sum'] or Decimal('0.00')
                # Asegurar Decimal
                if not isinstance(total, Decimal):
                    total = Decimal(str(total))
                self.importeTotal = total
                self.save()
    
    def quitar_producto(self, producto, cantidad=1):
        """
        Quita `cantidad` unidades de `producto` de esta cesta.

        `producto` puede ser una instancia de `productos.models.Producto` o su id (int).

        Comportamiento:
        - Si existe un ProductoCesta para (cesta, producto), decrementa la cantidad y actualiza el subtotal.
        - Si la cantidad llega a 0 o menos, elimina el ProductoCesta.
        - Recalcula y guarda `importeTotal` sumando los subtotales restantes.

        No hace nada si el producto no está en la cesta.
        Lanza ValueError si `cantidad` <= 0.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        # Importar localmente para evitar dependencias circulares en importación de módulos
        from productos.models import Producto, ProductoCesta
        # Resolver si nos pasan un id
        if isinstance(producto, int):
            producto = Producto.objects.get(pk=producto)

        with transaction.atomic():
            pc_qs = ProductoCesta.objects.select_for_update().filter(cesta=self, producto=producto)
            if pc_qs.exists():
                pc = pc_qs.first()
                pc.cantidad = pc.cantidad - cantidad
                if pc.cantidad > 0:
                    pc.subtotal = (Decimal(pc.cantidad) * producto.precio).quantize(Decimal('0.01'))
                    pc.save()
                else:
                    pc.delete()

                # Recalcular importeTotal sumando subtotales restantes
                total = ProductoCesta.objects.filter(cesta=self).aggregate(models.Sum('subtotal'))['subtotal__sum'] or Decimal('0.00')
                # Asegurar Decimal
                if not isinstance(total, Decimal):
                    total = Decimal(str(total))
                self.importeTotal = total
                self.save()

class Pago(models.Model):
    """Representa la información del pago para un Pedido."""
    # Atributos de tu diagrama:
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices)
    estadoPago = models.CharField(max_length=15, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    
    # Datos específicos del pago
    fechaPago = models.DateTimeField(auto_now_add=True)
    iTransaccion = models.CharField(max_length=100, blank=True, null=True, help_text="ID de la transacción devuelto por el proveedor de pagos (ej: Stripe).")

    class Meta:
        verbose_name = "Pago del Pedido"
        verbose_name_plural = "Pagos de Pedidos"
        
    def __str__(self):
        return f"Pago {self.id} - {self.metodo} - Estado: {self.estadoPago}"

class Pedido(models.Model):
    """Representa el pedido final, creado a partir de una Cesta."""
    # Relaciones y Datos del Pedido
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE) # Relación 1:1 con Pago
    cesta_asociada = models.OneToOneField(Cesta, on_delete=models.SET_NULL, null=True, help_text="Cesta Finalizada que originó este pedido.")
    
    fechaPedido = models.DateTimeField(auto_now_add=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2) 
    estado = models.CharField(max_length=15, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE) 

    # Información de Entrega
    tipoEntrega = models.CharField(max_length=20, choices=TipoEntrega.choices)
    
    # Copias estáticas de la información del cliente y entrega (para auditoría)
    nombre_cliente = models.CharField(max_length=150) 
    apellidos_cliente = models.CharField(max_length=150) 
    email_cliente = models.EmailField() 
    
    dirEntrega = models.ForeignKey(
        'Entrega', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pedidos_domicilio' # Ejemplo de related_name
    )
    puntoRecogida = models.ForeignKey(
        PuntoRecogidaPref, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pedidos_recogida' # Ejemplo de related_name
    )

    class Meta:
        verbose_name = "Pedido de Cliente"
        verbose_name_plural = "Pedidos de Clientes"

    def __str__(self):
        return f"Pedido N°{self.id} - Cliente: {self.nombre_cliente} - Importe: {self.importe}€"
    
    @property
    def productos_detalle(self):
        """Devuelve los productos que estaban en la cesta asociada."""
        if self.cesta_asociada:
            return ProductoCesta.objects.filter(cesta=self.cesta_asociada)
        return None
    
class Entrega(models.Model):
    """Representa la dirección física de entrega del pedido."""
    # idEntrega se crea automáticamente como el campo 'id'
    direccion = models.CharField(max_length=255)
    codigoPostal = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Información de Entrega"
        verbose_name_plural = "Información de Entregas"

    def __str__(self):
        return f"{self.direccion}, {self.ciudad} ({self.codigoPostal})"

class PuntoRecogida(models.Model):
    """Representa la dirección de un punto de recogida elegido para un pedido."""
    # idpunto es automático
    direccion = models.CharField(max_length=255)
    codigoPostal = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    horario = models.CharField(max_length=100) # Campo específico para el horario

    class Meta:
        verbose_name = "Punto de Recogida de Pedido"
        verbose_name_plural = "Puntos de Recogida de Pedidos"

    def __str__(self):
        return f"{self.direccion} ({self.horario})"
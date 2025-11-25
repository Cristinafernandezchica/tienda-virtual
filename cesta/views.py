from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages 
from decimal import Decimal # ✅ Necesario para el cálculo de precios

from productos.models import Producto
import stripe
from django.conf import settings

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .forms import CheckoutForm
from django.views.decorators.http import require_POST

from .models import (
    Cesta, Pedido, Pago, Entrega, PuntoRecogida, 
    TipoEntrega, MetodoPago, EstadoPedido, EstadoPago, EstadoCesta
)
from .forms import CheckoutForm
from cesta.utils import obtener_cesta, enviar_email_confirmacion
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect


stripe.api_key = settings.STRIPE_SECRET_KEY

# --- FUNCIONES AUXILIARES ---


def build_pedido_url(request, pedido):
    return request.build_absolute_uri(
        reverse('cesta:pedido_confirmacion', kwargs={'public_id': pedido.public_id})
    )


def calcular_gastos_envio(subtotal):
    """
    Calcula los gastos de envío:
    - 2.50€ si el subtotal es menor a 30€.
    - 0.00€ (Gratis) si es 30€ o más.
    """
    # Convertimos a Decimal si no lo es, para evitar errores de tipos
    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))
    
    if subtotal < Decimal('30.00'):
        return Decimal('2.50')
    return Decimal('0.00')


# --- FUNCIONES DE LÓGICA DE NEGOCIO ---

def actualizar_stock_y_ventas(pedido):
    """
    Actualiza el stock y las ventas de los productos en un pedido.
    Disminuye el stock con la cantidad comprada y aumenta las ventas.
    """
    try:
        with transaction.atomic():
            productos_cesta = pedido.cesta_asociada.producto_cestas.all()
            
            for item_cesta in productos_cesta:
                # Bloqueamos el producto para evitar condiciones de carrera
                producto = Producto.objects.select_for_update().get(pk=item_cesta.producto.pk)
                cantidad_comprada = item_cesta.cantidad
                
                if producto.stock >= cantidad_comprada:
                    producto.stock -= cantidad_comprada
                else:
                    print(f"ERROR: Stock insuficiente para Producto {producto.id}.")
                    
                producto.vendidos += cantidad_comprada
                producto.save()
        print(f"Stock y ventas actualizados exitosamente para el Pedido {pedido.id}")
    except Exception as e:
        print(f"Error al actualizar stock/ventas para el Pedido {pedido.id}: {e}")


def _get_or_create_cesta_from_session(request):
    """Función auxiliar que crea la cesta para la sesión si no existe."""
    cesta_id = request.session.get('cesta_id')
    if cesta_id:
        try:
            cesta = Cesta.objects.get(pk=cesta_id, estadoCesta=EstadoCesta.ABIERTA)
            return cesta
        except Cesta.DoesNotExist:
            request.session.pop('cesta_id', None)

    cesta = Cesta.objects.create(estadoCesta=EstadoCesta.ABIERTA)
    request.session['cesta_id'] = cesta.id
    request.session.modified = True
    return cesta


def ver_cesta(request):
    """Vista para mostrar la cesta con el cálculo de envío."""
    cesta = obtener_cesta(request)
    
    # Calcular totales para mostrar en el HTML de la cesta
    subtotal = cesta.importeTotal
    gastos_envio = calcular_gastos_envio(subtotal)
    total_con_envio = subtotal + gastos_envio

    context = {
        'cesta': cesta,
        'gastos_envio': gastos_envio,     # Pasar al template
        'total_con_envio': total_con_envio # Pasar al template
    }
    return render(request, 'cesta.html', context)

def añadir_a_cesta(request, producto_id, cantidad=None):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
    
    if cantidad > producto.stock:
        cantidad = producto.stock
    
    cesta = obtener_cesta(request)
    try:
        cesta.añadir_producto(producto_id, cantidad)
    except ValueError as e:
        messages.error(request, str(e) or "No se puede añadir más unidades: stock insuficiente.")
    else:
        messages.success(request, f"Has añadido {cantidad} artículo(s) a la cesta correctamente.")

    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))


def eliminar_de_cesta(request, producto_id):
    """Vista para eliminar un producto de la cesta."""
    cesta = obtener_cesta(request)
    cesta.eliminar_producto(producto_id)
    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))

def añadir_producto_a_cesta(request, producto_id, cantidad):
    """Vista para añadir un producto a la cesta."""
    cesta = obtener_cesta(request)
    try:
        cesta.añadir_producto(producto_id, cantidad)
    except ValueError as e:
        messages.error(request, str(e) or "No se puede añadir más unidades: stock insuficiente.")
    else:
        messages.success(request, "Producto añadido a la cesta.")

    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))

def quitar_producto_de_cesta(request, producto_id):
    """Vista para quitar una unidad de producto de la cesta."""
    cesta = obtener_cesta(request)
    cesta.quitar_producto(producto_id)
    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))

# Vistas Dummy


def pago_externo_simulacion(request, public_id):
    """Simulación de la pasarela de pago usando public_id."""
    pedido = get_object_or_404(Pedido, public_id=public_id)
    return render(request, 'cesta/pago_simulacion.html', {'pedido': pedido})


def pedido_confirmacion(request, public_id):
    pedido = get_object_or_404(Pedido, public_id=public_id)
    return render(request, 'cesta/pedido_confirmacion.html', {'pedido': pedido})


def checkout_view(request):
    """
    Vista que maneja la selección de datos de envío/pago y crea el Pedido final.
    """
    
    user = request.user
    
    # 1. Obtener la Cesta Activa
    try:
        cesta = obtener_cesta(request)
    except Exception as e:
        print(f"Error al obtener la cesta en checkout: {e}")
        return redirect(reverse_lazy('cesta:ver_cesta')) 

    if not cesta.producto_cestas.exists() or cesta.importeTotal <= 0:
        return redirect(reverse_lazy('cesta:ver_cesta'))
    
    # Validamos que no haya productos con cantidad mayor al stock disponible
    for pc in cesta.producto_cestas.all():
        if pc.cantidad > pc.producto.stock:
            messages.error(
                request,
                f"El producto '{pc.producto.nombre}' no tiene stock suficiente. "
            )
            return redirect('cesta:ver_cesta')

    # Calcular totales para el Pedido (incluyendo envío)
    subtotal = cesta.importeTotal
    gastos_envio = calcular_gastos_envio(subtotal)
    total_pedido = subtotal + gastos_envio

    # Búsqueda del pedido anterior fallido para precarga
    pedido_fallido = None
    try:
        pedido_fallido = Pedido.objects.filter(
            cesta_asociada=cesta, 
            estado=EstadoPedido.PENDIENTE 
        ).order_by('-fechaPedido').first()
    except Exception as e:
        print(f"Error al buscar pedido fallido: {e}")
        
    # 2. Manejo del Formulario
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=user, pedido_fallido=pedido_fallido) 
        if form.is_valid():
            datos = form.cleaned_data
            
            # Desvincular pedido fallido si existe
            if pedido_fallido:
                 pedido_fallido.cesta_asociada = None
                 pedido_fallido.save()
            
            with transaction.atomic():
                
                # --- Lógica de Estados Iniciales ---
                metodo_pago_seleccionado = datos['metodo_pago']
                
                if metodo_pago_seleccionado == MetodoPago.CONTRAREEMBOLSO:
                    estado_pago = EstadoPago.PENDIENTE
                    estado_pedido = EstadoPedido.EN_PREPARACION
                else:
                    estado_pago = EstadoPago.PENDIENTE 
                    estado_pedido = EstadoPedido.PENDIENTE
                # --------------------------------
                
                
                # 3. Crear instancia de Pago 
                pago = Pago.objects.create(
                    metodo=metodo_pago_seleccionado,
                    estadoPago=estado_pago, 
                )

                # 4. Crear instancias de Entrega/PuntoRecogida 
                entrega_obj = None
                punto_recogida_obj = None

                if datos['tipo_entrega'] == TipoEntrega.DOMICILIO:
                    entrega_obj = Entrega.objects.create(
                        direccion=datos['direccion_envio'],
                        codigoPostal=datos['codigoPostal_envio'],
                        ciudad=datos['ciudad_envio'],
                        pais=datos['pais_envio'],
                    )
                
                elif datos['tipo_entrega'] == TipoEntrega.PUNTO_RECOGIDA:
                    punto_recogida_obj = datos['punto_recogida']


                # 5. Crear el Pedido
                pedido = Pedido.objects.create(
                    usuario=user if user.is_authenticated else None, 
                    pago=pago,
                    cesta_asociada=cesta, 
                    importe=total_pedido, # Guardamos el total CON envío
                    estado=estado_pedido,
                    
                    nombre_cliente=datos['nombre_cliente'],
                    apellidos_cliente=datos['apellidos_cliente'],
                    email_cliente=datos['email_cliente'],
                    
                    tipoEntrega=datos['tipo_entrega'],
                    dirEntrega=entrega_obj,
                    puntoRecogida=punto_recogida_obj
                )
                
                # 6. Envio de Email (Debe ser asíncrono o configurado)
                # Por ahora comentado o manejado en utils si está configurado
                
                # 9. Actualizar stock si procede
                if estado_pedido == EstadoPedido.EN_PREPARACION:
                    actualizar_stock_y_ventas(pedido)
                
                # 10. Finalizar cesta
                cesta.estadoCesta = EstadoCesta.FINALIZADA 
                cesta.save()
                
                # 11. Limpiar sesión de invitados
                if not user.is_authenticated and 'cesta_id' in request.session:
                    request.session.pop('cesta_id')
                
                # 12. Redirecciones finales
                if datos['metodo_pago'] == MetodoPago.CONTRAREEMBOLSO:
                    # --------------- ENVÍO EMAIL ----------------
                    try:
                        pedido_url = build_pedido_url(request, pedido)
                        enviar_email_confirmacion(pedido, pedido_url)
                        print(f"Email de contrareembolso enviado para el pedido {pedido.id}")
                    except Exception as e:
                        print("Error enviando email de contrareembolso:", e)
                    # --------------------------------------------

                    return redirect('cesta:pedido_confirmacion', public_id=pedido.public_id)

                # Redirige a la pasarela Stripe para Tarjeta
                return redirect('cesta:stripe_checkout', pedido_id=pedido.id)
        else:
            pass 
    else:
        form = CheckoutForm(user=user, pedido_fallido=pedido_fallido)

    # Pasamos los totales al contexto para que checkout.html pueda mostrarlos
    context = {
        'form': form, 
        'cesta': cesta,
        'gastos_envio': gastos_envio,
        'total_con_envio': total_pedido
    }
    return render(request, 'cesta/checkout.html', context)


def pago_exito(request, public_id):
    pedido = get_object_or_404(Pedido, public_id=public_id)

    # ---- 1. Cambiar estado del pago ----
    if pedido.pago.estadoPago == EstadoPago.PENDIENTE:
        pedido.pago.estadoPago = EstadoPago.COMPLETADO
        pedido.pago.save()

    # ---- 2. Si el pedido estaba pendiente, actualizamos stock y estado ----
    if pedido.estado == EstadoPedido.PENDIENTE:
        pedido.estado = EstadoPedido.EN_PREPARACION
        pedido.save()
        actualizar_stock_y_ventas(pedido)

        # ---- 3. Envío de email de confirmación ----
        try:
            pedido_url = build_pedido_url(request, pedido)
            enviar_email_confirmacion(pedido, pedido_url)
            print(f"Email enviado correctamente para el pedido {pedido.id}")
        except Exception as e:
            print("Error enviando el email:", e)

    # ---- 4. Renderizar pantalla de éxito ----
    return render(request, 'cesta/pago_exito.html', {'pedido': pedido})


def pago_fallo(request, public_id):
    """Maneja la cancelación o fallo del pago."""
    pedido = get_object_or_404(Pedido, public_id=public_id)
    
    cesta_finalizada = pedido.cesta_asociada
    if cesta_finalizada and cesta_finalizada.estadoCesta == EstadoCesta.FINALIZADA:
        cesta_finalizada.estadoCesta = EstadoCesta.ABIERTA
        cesta_finalizada.save()
        
        pedido.cesta_asociada = None
        pedido.estado = EstadoPedido.PENDIENTE 
        pedido.save()

        if not request.user.is_authenticated:
            request.session['cesta_id'] = cesta_finalizada.id
            request.session.modified = True
    
    return render(request, 'cesta/pago_fallo.html', {'pedido': pedido})

def stripe_checkout(request, pedido_id):
    """Crea una sesión de Stripe Checkout y redirige al usuario."""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    line_items = []
    
    # Añadir productos
    for item in pedido.cesta_asociada.producto_cestas.all():
        line_items.append({
            'price_data': {
                'currency': 'eur', 
                'unit_amount': int(item.subtotal / item.cantidad * 100), 
                'product_data': {
                    'name': item.producto.nombre,
                },
            },
            'quantity': item.cantidad,
        })

    # Añadir gastos de envío a Stripe si corresponde
    # Calculamos la diferencia entre lo que se guardó en el Pedido y lo que valía la Cesta
    gastos_envio = pedido.importe - pedido.cesta_asociada.importeTotal
    
    if gastos_envio > 0:
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(gastos_envio * 100), # Convertir a céntimos
                'product_data': {
                    'name': 'Gastos de Envío',
                    'description': 'Tarifa plana de envío'
                },
            },
            'quantity': 1,
        })

    try:
        # 2. Crear la sesión de Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse_lazy('cesta:pago_exito', kwargs={'public_id': pedido.public_id})),
            cancel_url=request.build_absolute_uri(reverse_lazy('cesta:pago_fallo', kwargs={'public_id': pedido.public_id})),
            metadata={'pedido_id': pedido.id},
        )
        return redirect(session.url, code=303)
    
    except Exception as e:
        print(f"Error al crear sesión de Stripe: {e}")
        messages.error(request, "Error interno al iniciar el pago. Inténtelo de nuevo.")
        return redirect(reverse_lazy('cesta:checkout'))


@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fechaPedido')
    return render(request, 'cesta/mis_pedidos.html', {'pedidos': pedidos})


def es_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'rol', '') == 'ADMIN')


@user_passes_test(es_admin)
def pedido_admin_detalle(request, public_id):
    """Detalle de pedido para administradores usando public_id."""
    pedido = get_object_or_404(Pedido, public_id=public_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get("estado")
        if nuevo_estado in EstadoPedido.values:
            pedido.estado = nuevo_estado
            pedido.save()

        # Redirigimos con public_id, NO con el id interno
        return redirect(reverse('cesta:pedido_admin_detalle', kwargs={'public_id': pedido.public_id}))

    return render(request, 'cesta/pedido_admin_detalle.html', {
        'pedido': pedido,
        'Estados': EstadoPedido,
    })


@user_passes_test(es_admin)
def lista_pedidos_admin(request):
    pedidos = Pedido.objects.all()

    # --- Filtros desde GET ---
    query = request.GET.get("q")
    estado = request.GET.get("estado")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    importe_min = request.GET.get("importe_min")
    importe_max = request.GET.get("importe_max")
    orden = request.GET.get("orden")

    # Búsqueda general (ID, cliente, email)
    if query:
        pedidos = pedidos.filter(
            Q(public_id__icontains=query) |
            Q(nombre_cliente__icontains=query) |
            Q(apellidos_cliente__icontains=query) |
            Q(email_cliente__icontains=query)
        )

    # Estado
    if estado:
        pedidos = pedidos.filter(estado=estado)

    # Fechas
    if fecha_desde:
        pedidos = pedidos.filter(fechaPedido__date__gte=parse_date(fecha_desde))
    if fecha_hasta:
        pedidos = pedidos.filter(fechaPedido__date__lte=parse_date(fecha_hasta))

    # Importe
    if importe_min:
        pedidos = pedidos.filter(importe__gte=importe_min)
    if importe_max:
        pedidos = pedidos.filter(importe__lte=importe_max)

    # Orden
    if orden == "fecha_asc":
        pedidos = pedidos.order_by("fechaPedido")
    elif orden == "fecha_desc":
        pedidos = pedidos.order_by("-fechaPedido")
    elif orden == "importe_asc":
        pedidos = pedidos.order_by("importe")
    elif orden == "importe_desc":
        pedidos = pedidos.order_by("-importe")
    else:
        pedidos = pedidos.order_by("-fechaPedido")  # por defecto

    return render(
        request,
        "cesta/lista_pedidos_admin.html",
        {
            "pedidos": pedidos,
            "query": query,
            "estado_seleccionado": estado,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "importe_min": importe_min,
            "importe_max": importe_max,
            "orden_seleccionado": orden,
        },
    )


def añadir_producto_compra_rapida(request, producto_id):
    cantidad = int(request.POST.get('cantidad', 1))
    accion = request.POST.get('accion')

    if accion == 'añadir_producto':
        return añadir_a_cesta(request, producto_id, cantidad)
    elif accion == 'compra_rapida':
        añadir_a_cesta(request, producto_id, cantidad)
        return redirect('cesta:checkout')
    else:
        messages.error(request, "Acción no reconocida.")
        return redirect('catalogo')

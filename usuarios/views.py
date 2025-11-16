from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .forms import UsuarioRegisterForm, DireccionPrefForm, PuntoRecogidaPrefForm, MetodoPagoForm
from .models import DireccionPref, PuntoRecogidaPref, Usuario

def es_admin(user):
    return user.is_authenticated and user.rol == 'ADMIN'

def register(request):
    if request.method == 'POST':
        form = UsuarioRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # el save() del formulario ya guarda el rol (Cliente por defecto o Administrador si se selecciona)
            auth_login(request, user)   # loguea automáticamente tras registro
            return redirect('catalogo')  # redirige a la página principal / catálogo
    else:
        form = UsuarioRegisterForm()
    return render(request, 'usuarios/register.html', {'form': form})


@login_required
def datos_entrega(request):
    user = request.user

    # Formularios para la vista de datos de entrega
    if request.method == 'POST':
        form_pago = MetodoPagoForm(request.POST, instance=user)
        form_direccion = DireccionPrefForm(request.POST)
        form_punto = PuntoRecogidaPrefForm(request.POST)

        # Guardar método de pago
        if 'guardar_pago' in request.POST and form_pago.is_valid():
            form_pago.save()
            messages.success(request, "Método de pago preferente guardado correctamente.")
            return redirect('usuarios:datos_entrega')

        # Guardar dirección
        if 'guardar_direccion' in request.POST and form_direccion.is_valid():
            direccion = form_direccion.save(commit=False)
            direccion.usuario = user
            direccion.save()
            if 'set_preferida' in request.POST:
                user.direccion_preferida = direccion
                user.save()
            return redirect('usuarios:datos_entrega')

        # Guardar punto de recogida
        if 'guardar_punto' in request.POST and form_punto.is_valid():
            punto = form_punto.save(commit=False)
            punto.usuario = user
            punto.save()
            if 'set_preferido' in request.POST:
                user.punto_recogida_pref = punto
                user.save()
            return redirect('usuarios:datos_entrega')

    else:
        form_pago = MetodoPagoForm(instance=user)
        form_direccion = DireccionPrefForm()
        form_punto = PuntoRecogidaPrefForm()

    # Obtener direcciones y puntos de recogida asociados al usuario
    # Usamos los related_name definidos en los modelos
    direcciones = user.direcciones.all()
    puntos = PuntoRecogidaPref.objects.all().order_by('ciudad')

    return render(request, 'usuarios/datos_entrega.html', {
        'form_pago': form_pago,
        'form_direccion': form_direccion,
        'form_punto': form_punto,
        'direcciones': direcciones,
        'puntos': puntos,
    })

@user_passes_test(es_admin)
def datos_puntos(request):
    user = request.user

    # Formularios para la vista de datos de entrega
    if request.method == 'POST':
        form_punto = PuntoRecogidaPrefForm(request.POST)

        # Guardar punto de recogida
        if 'guardar_punto' in request.POST and form_punto.is_valid():
            punto = form_punto.save(commit=False)
            punto.usuario = user
            punto.save()
            if 'set_preferido' in request.POST:
                user.punto_recogida_pref = punto
                user.save()
            return redirect('usuarios:gestion_puntos')

    else:
        form_punto = PuntoRecogidaPrefForm()

    # Obtener direcciones y puntos de recogida asociados al usuario
    # Usamos los related_name definidos en los modelos
    puntos = PuntoRecogidaPref.objects.all()

    return render(request, 'usuarios/gestion_puntos.html', {
        'form_punto': form_punto,
        'puntos': puntos,
        'usuario_actual': request.user,
    })


@login_required
def add_direccion(request):
    if request.method == 'POST':
        form = DireccionPrefForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.usuario = request.user
            direccion.save()
            msg = "Nueva dirección guardada correctamente."
            if 'set_preferida' in request.POST:
                request.user.direccion_preferida = direccion
                request.user.save()
                msg = "Nueva dirección guardada y marcada como **preferida**."
            messages.success(request, msg)
            return redirect('usuarios:datos_entrega')
    else:
        form = DireccionPrefForm()
    return render(request, 'usuarios/address_form.html', {'form': form})


@user_passes_test(es_admin)
def add_punto_recogida(request):
    if request.method == 'POST':
        form = PuntoRecogidaPrefForm(request.POST)
        if form.is_valid():
            punto = form.save(commit=False)
            punto.usuario = request.user
            punto.save()
            if 'set_preferido' in request.POST:
                request.user.punto_recogida_pref = punto
                request.user.save()
            return redirect('usuarios:gestion_puntos')
    else:
        form = PuntoRecogidaPrefForm()
    return render(request, 'usuarios/pickup_form.html', {'form': form})


@user_passes_test(es_admin)
def lista_clientes(request):
    clientes = Usuario.objects.filter(rol='CLIENTE').order_by('username')
    return render(request, 'usuarios/lista_clientes.html', {'clientes': clientes})


@login_required
def editar_direccion(request, id):
    direccion = get_object_or_404(DireccionPref, id=id, usuario=request.user)
    if request.method == 'POST':
        form = DireccionPrefForm(request.POST, instance=direccion)
        if form.is_valid():
            form.save()
            messages.success(request, "Dirección actualizada correctamente.")
            return redirect('usuarios:datos_entrega')
    else:
        form = DireccionPrefForm(instance=direccion)
    return render(request, 'usuarios/address_form.html', {'form': form})

@login_required
def eliminar_direccion(request, id):
    direccion = get_object_or_404(DireccionPref, id=id, usuario=request.user)
    if request.method == 'POST':
        direccion.delete()
        if request.user.direccion_preferida_id == id:
            request.user.direccion_preferida = None
            request.user.save()
        
        messages.success(request, f"La dirección '{direccion.direccion}' ha sido eliminada.")
        return redirect('usuarios:datos_entrega')
    return render(request, 'usuarios/confirmar_eliminacion.html', {'direccion': direccion})

@login_required
def preferida_direccion(request, id):
    direccion = get_object_or_404(DireccionPref, id=id, usuario=request.user)
    request.user.direccion_preferida = direccion
    request.user.save()
    
    messages.success(request, f"Dirección {direccion.direccion} marcada como preferida.")
    return redirect('usuarios:datos_entrega')


@user_passes_test(es_admin)
def editar_punto(request, id):
    punto = get_object_or_404(PuntoRecogidaPref, id=id)
    if request.method == 'POST':
        form = PuntoRecogidaPrefForm(request.POST, instance=punto)
        if form.is_valid():
            form.save()
            return redirect('usuarios:gestion_puntos')
    else:
        form = PuntoRecogidaPrefForm(instance=punto)
    return render(request, 'usuarios/pickup_form.html', {'form': form})

@user_passes_test(es_admin)
def eliminar_punto(request, id):
    punto = get_object_or_404(PuntoRecogidaPref, id=id)
    if request.method == 'POST':
        punto.delete()
    return redirect('usuarios:gestion_puntos')

@login_required
def preferido_punto(request, id):
    punto = get_object_or_404(PuntoRecogidaPref, id=id)
    request.user.punto_recogida_pref = punto
    request.user.save()
    
    messages.success(request, f"Punto de recogida '{punto.direccion}' marcado como preferido.")
    return redirect('usuarios:datos_entrega')

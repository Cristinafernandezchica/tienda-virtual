from django import forms
from django.utils.translation import gettext_lazy as _
from usuarios.models import DireccionPref, PuntoRecogidaPref # Modelos de la app usuarios
from .models import TipoEntrega, MetodoPago as PagoMetodoChoices 
from .models import PuntoRecogida # Necesario para ModelChoiceField
import re
from django.core.exceptions import ValidationError


class CheckoutForm(forms.Form):
    """
    Formulario unificado para Checkout. Precarga los datos del usuario logueado 
    o del último pedido fallido.
    """
    
    # --- Datos del Cliente (Auditoría) ---
    nombre_cliente = forms.CharField(max_length=150, label=_("Nombre"))
    apellidos_cliente = forms.CharField(max_length=150, label=_("Apellidos"))
    email_cliente = forms.EmailField(label=_("Email de Contacto"))

    # --- Tipo de Entrega y Pago ---
    tipo_entrega = forms.ChoiceField(
        choices=TipoEntrega.choices, 
        widget=forms.RadioSelect, 
        label=_("Método de Entrega")
    )
    metodo_pago = forms.ChoiceField(
        choices=PagoMetodoChoices.choices, 
        widget=forms.RadioSelect, 
        label=_("Método de Pago")
    )
    
    # --- Campos para Dirección de Envío (Domicilio) ---
    direccion_envio = forms.CharField(max_length=255, required=False, label=_("Dirección"))
    codigoPostal_envio = forms.CharField(max_length=10, required=False, label=_("Código Postal"))
    ciudad_envio = forms.CharField(max_length=100, required=False, label=_("Ciudad"))
    pais_envio = forms.CharField(max_length=100, required=False, label=_("País"))
    
    # --- Campos para Punto de Recogida (Selección de un objeto existente) ---
    punto_recogida = forms.ModelChoiceField(
        # Usamos PuntoRecogidaPref para listar los puntos elegibles
        queryset=PuntoRecogidaPref.objects.all(),
        required=False,
        label=_("Selecciona un Punto de Recogida"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, user=None, pedido_fallido=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar clase CSS 'form-control' a la mayoría de los widgets
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
                 field.widget.attrs['class'] = 'form-control'
        
        datos_iniciales = {}

        # 1. Precarga por Perfil (Solo si el usuario está autenticado)
        if user and user.is_authenticated:
            datos_iniciales['nombre_cliente'] = user.nombre
            datos_iniciales['apellidos_cliente'] = user.apellidos
            datos_iniciales['email_cliente'] = user.email
            
            try:
                # Intenta usar DireccionPref (asumo que se accede por related_name 'direccion_preferida')
                dir_pref = user.direccion_preferida
                if dir_pref:
                    datos_iniciales['direccion_envio'] = dir_pref.direccion
                    datos_iniciales['codigoPostal_envio'] = dir_pref.codigoPostal
                    datos_iniciales['ciudad_envio'] = dir_pref.ciudad
                    datos_iniciales['pais_envio'] = dir_pref.pais
            except DireccionPref.DoesNotExist:
                pass
            
            try:
                # Intenta usar PuntoRecogidaPref
                punto_pref = user.punto_recogida_pref
                if punto_pref:
                    datos_iniciales['punto_recogida'] = punto_pref # ModelChoiceField espera la instancia
            except PuntoRecogidaPref.DoesNotExist:
                pass

            if user.metodoPagoPref:
                datos_iniciales['metodo_pago'] = user.metodoPagoPref


        # ⭐️ 2. SOBRESCRIBIR CON DATOS DEL PEDIDO FALLIDO (PRIORIDAD) ⭐️
        # Si un pedido fallido existe, sus datos son más recientes que la preferencia del perfil.
        if pedido_fallido:
            # Datos del Cliente
            datos_iniciales['nombre_cliente'] = pedido_fallido.nombre_cliente
            datos_iniciales['apellidos_cliente'] = pedido_fallido.apellidos_cliente
            datos_iniciales['email_cliente'] = pedido_fallido.email_cliente
            
            # Método de Entrega/Pago
            datos_iniciales['tipo_entrega'] = pedido_fallido.tipoEntrega
            datos_iniciales['metodo_pago'] = pedido_fallido.pago.metodo

            # Detalles de Entrega
            if pedido_fallido.dirEntrega:
                datos_iniciales['direccion_envio'] = pedido_fallido.dirEntrega.direccion
                datos_iniciales['codigoPostal_envio'] = pedido_fallido.dirEntrega.codigoPostal
                datos_iniciales['ciudad_envio'] = pedido_fallido.dirEntrega.ciudad
                datos_iniciales['pais_envio'] = pedido_fallido.dirEntrega.pais
            
            # Detalles de Punto de Recogida
            if pedido_fallido.puntoRecogida:
                # ModelChoiceField espera el objeto PuntoRecogida (que es un ForeignKey, por lo tanto, una instancia)
                datos_iniciales['punto_recogida'] = pedido_fallido.puntoRecogida

        # Aplicar datos iniciales
        for key, value in datos_iniciales.items():
            if value is not None:
                self.fields[key].initial = value

        # 3. Sobrescribir el método clean para la validación dinámica
        self.clean = self._conditional_clean

    def _conditional_clean(self):
        """Valida que los campos de dirección o punto de recogida estén llenos 
        dependiendo del 'tipo_entrega' seleccionado.
        """
        cleaned_data = super().clean()
        tipo_entrega = cleaned_data.get('tipo_entrega')

        if tipo_entrega == TipoEntrega.DOMICILIO:
            required_fields = ['direccion_envio', 'codigoPostal_envio', 'ciudad_envio', 'pais_envio']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _("Este campo es obligatorio para la entrega a domicilio."))
            
            # --- Validación de Dirección ---
            direccion = cleaned_data.get('direccion_envio')
            if direccion:
                # Debe contener al menos una letra, al menos un número y al menos una coma
                if not re.match(r'^(?=.*[A-Za-zÀ-ÿ])(?=.*\d)(?=.*[,])[A-Za-zÀ-ÿ0-9\s.,ºª-]+$', direccion):
                    self.add_error(
                        'direccion_envio',
                        _("La dirección debe contener al menos una letra, un número y una coma, y solo puede incluir letras, números, espacios, comas, puntos, º, ª o guion.")
                    )

            # --- Validación de Código Postal ---
            codigo_postal = cleaned_data.get('codigoPostal_envio')
            if codigo_postal:
                if not re.fullmatch(r'\d{5}', codigo_postal):
                    self.add_error('codigoPostal_envio', _("El código postal debe tener exactamente 5 dígitos."))

            # --- Validación de Ciudad ---
            ciudad = cleaned_data.get('ciudad_envio')
            if ciudad:
                if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', ciudad):
                    self.add_error('ciudad_envio', _("La ciudad solo puede contener letras y espacios."))

            # --- Validación de País ---
            pais = cleaned_data.get('pais_envio')
            if pais:
                if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', pais):
                    self.add_error('pais_envio', _("El país solo puede contener letras y espacios."))

        elif tipo_entrega == TipoEntrega.PUNTO_RECOGIDA:
            # Solo necesita validar que se haya seleccionado un objeto PointRecogida
            if not cleaned_data.get('punto_recogida'):
                self.add_error('punto_recogida', _("Debes seleccionar un punto de recogida."))

        return cleaned_data
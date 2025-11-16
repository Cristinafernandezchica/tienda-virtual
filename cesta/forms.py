from django import forms
from django.utils.translation import gettext_lazy as _
from usuarios.models import DireccionPref, PuntoRecogidaPref # Modelos de la app usuarios
# CORRECCIÓN CLAVE: Importamos directamente desde el models.py local
from .models import TipoEntrega, MetodoPago as PagoMetodoChoices 

class CheckoutForm(forms.Form):
    """
    Formulario unificado para Checkout. Precarga la dirección del usuario autenticado 
    en campos de texto editables y valida dinámicamente según el tipo de entrega.
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
    # Son required=False a nivel de campo, se validan como requeridos en .clean()
    direccion_envio = forms.CharField(max_length=255, required=False, label=_("Dirección"))
    codigoPostal_envio = forms.CharField(max_length=10, required=False, label=_("Código Postal"))
    ciudad_envio = forms.CharField(max_length=100, required=False, label=_("Ciudad"))
    pais_envio = forms.CharField(max_length=100, required=False, label=_("País"))
    
    # --- Campos para Punto de Recogida ---
    punto_recogida = forms.ModelChoiceField(
        queryset=PuntoRecogidaPref.objects.all(),
        required=False,
        label=_("Selecciona un Punto de Recogida"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # punto_direccion = forms.CharField(max_length=255, required=False, label=_("Dirección del Punto"))
    # punto_codigoPostal = forms.CharField(max_length=10, required=False, label=_("Código Postal del Punto"))
    # punto_ciudad = forms.CharField(max_length=100, required=False, label=_("Ciudad del Punto"))
    # punto_pais = forms.CharField(max_length=100, required=False, label=_("País del Punto"))
    # punto_horario = forms.CharField(max_length=255, required=False, label=_("Horario de Recogida"))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar clase CSS 'form-control' a la mayoría de los widgets de texto/número/select
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
                 field.widget.attrs['class'] = 'form-control'
        
        if user and user.is_authenticated:
            # 1. Precargar datos personales del usuario logueado
            self.fields['nombre_cliente'].initial = user.nombre
            self.fields['apellidos_cliente'].initial = user.apellidos
            self.fields['email_cliente'].initial = user.email
            
            # 2. Intentar precargar la dirección de envío preferida (editable)
            try:
                dir_pref = user.direccion_preferida
                if dir_pref:
                    self.fields['direccion_envio'].initial = dir_pref.direccion
                    self.fields['codigoPostal_envio'].initial = dir_pref.codigoPostal
                    self.fields['ciudad_envio'].initial = dir_pref.ciudad
                    self.fields['pais_envio'].initial = dir_pref.pais
            except DireccionPref.DoesNotExist:
                pass

            # 3. Intentar precargar el punto de recogida preferido (editable)
            try:
                punto_pref = user.punto_recogida_pref
                if punto_pref:
                    self.fields['punto_recogida'].initial = punto_pref
            except PuntoRecogidaPref.DoesNotExist:
                pass

            # 4. Precargar método de pago preferido
            if user and user.is_authenticated and user.metodoPagoPref:
                self.fields['metodo_pago'].initial = user.metodoPagoPref
        
        # 4. Sobrescribir el método clean para la validación dinámica
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
        
        elif tipo_entrega == TipoEntrega.PUNTO_RECOGIDA:
            if not cleaned_data.get('punto_recogida'):
                self.add_error('punto_recogida', _("Debes seleccionar un punto de recogida."))

        return cleaned_data
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, DireccionPref, PuntoRecogidaPref
from django.contrib.auth import authenticate, get_user_model
import re


class UsuarioRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    nombre = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellidos = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Campo para el rol (Cliente por defecto, opción Administrador)
    rol = forms.ChoiceField(
        choices=Usuario._meta.get_field('rol').choices,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=False,
        initial=Usuario._meta.get_field('rol').default  # CLIENTE por defecto
    )

    # Campos de contraseña
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'nombre', 'apellidos',
            'rol', 'password1', 'password2'
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nombre = self.cleaned_data.get('nombre', '')
        user.apellidos = self.cleaned_data.get('apellidos', '')
        user.rol = self.cleaned_data.get('rol') or Usuario._meta.get_field('rol').default

        if commit:
            user.save()
        return user


class DireccionPrefForm(forms.ModelForm):
    class Meta:
        model = DireccionPref
        fields = ['direccion', 'codigoPostal', 'ciudad', 'pais']
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'codigoPostal': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        direccion = cleaned_data.get('direccion')
        codigo_postal = cleaned_data.get('codigoPostal')
        ciudad = cleaned_data.get('ciudad')
        pais = cleaned_data.get('pais')

        # --- Validación Dirección ---
        if direccion:
            # Debe contener al menos una letra, un número y una coma, y solo símbolos permitidos
            if not re.match(r'^(?=.*[A-Za-zÀ-ÿ])(?=.*\d)(?=.*[,])[A-Za-zÀ-ÿ0-9\s.,ºª-]+$', direccion):
                self.add_error(
                    'direccion',
                    "La dirección debe contener al menos una letra, un número y una coma, "
                    "y solo puede incluir letras, números, espacios, comas, puntos, º, ª o guion."
                )

        # --- Validación Código Postal ---
        if codigo_postal:
            if not re.fullmatch(r'\d{5}', codigo_postal):
                self.add_error('codigoPostal', "El código postal debe tener exactamente 5 dígitos.")

        # --- Validación Ciudad ---
        if ciudad:
            if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', ciudad):
                self.add_error('ciudad', "La ciudad solo puede contener letras y espacios.")

        # --- Validación País ---
        if pais:
            if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', pais):
                self.add_error('pais', "El país solo puede contener letras y espacios.")

        return cleaned_data


class PuntoRecogidaPrefForm(forms.ModelForm):
    class Meta:
        model = PuntoRecogidaPref
        fields = ['direccion', 'codigoPostal', 'ciudad', 'pais', 'horario']
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'codigoPostal': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'horario': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        direccion = cleaned_data.get('direccion')
        codigo_postal = cleaned_data.get('codigoPostal')
        ciudad = cleaned_data.get('ciudad')
        pais = cleaned_data.get('pais')

        # --- Validación Dirección ---
        if direccion:
            # Debe contener al menos una letra, un número y una coma, y solo símbolos permitidos
            if not re.match(r'^(?=.*[A-Za-zÀ-ÿ])(?=.*\d)(?=.*[,])[A-Za-zÀ-ÿ0-9\s.,ºª-]+$', direccion):
                self.add_error(
                    'direccion',
                    "La dirección debe contener al menos una letra, un número y una coma, "
                    "y solo puede incluir letras, números, espacios, comas, puntos, º, ª o guion."
                )

        # --- Validación Código Postal ---
        if codigo_postal:
            if not re.fullmatch(r'\d{5}', codigo_postal):
                self.add_error('codigoPostal', "El código postal debe tener exactamente 5 dígitos.")

        # --- Validación Ciudad ---
        if ciudad:
            if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', ciudad):
                self.add_error('ciudad', "La ciudad solo puede contener letras y espacios.")

        # --- Validación País ---
        if pais:
            if not re.fullmatch(r'[A-Za-zÀ-ÿ\s]+', pais):
                self.add_error('pais', "El país solo puede contener letras y espacios.")

        return cleaned_data


class MetodoPagoForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['metodoPagoPref']  # solo este campo
        widgets = {
            'metodoPagoPref': forms.RadioSelect  # muestra como botones
        }
        labels = {
            'metodoPagoPref': 'Método de pago preferente'
        }

Usuario = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:
            try:
                # Si lo que escribió es un correo, buscamos el username asociado
                user_obj = Usuario.objects.get(email=username_or_email)
                username = user_obj.username
            except Usuario.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
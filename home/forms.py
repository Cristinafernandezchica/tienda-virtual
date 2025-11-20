from django import forms
from django.core.validators import RegexValidator
from .models import ContactInfo


phone_validator = RegexValidator(
    regex=r'^\+?[0-9\s()\-]{7,20}$',
    message='Número de teléfono inválido. Use sólo dígitos, espacios, paréntesis, guiones y un + opcional.'
)


class ContactInfoForm(forms.ModelForm):
    telefono = forms.CharField(
        required=True,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 600 000 000',
            'pattern': '\\+?[0-9\\s()\\-]{7,20}',
            'required': 'required'
        })
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force all form fields to be required (so template shows asterisk)
        for name, field in self.fields.items():
            field.required = True
        # Set spanish labels with proper accents
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo electrónico',
        }
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label

    class Meta:
        model = ContactInfo
        fields = ['nombre', 'descripcion', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200, 'required': True}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'maxlength': 1000, 'required': True}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 255, 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@ejemplo.com', 'required': True}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        nombre = nombre.strip()
        if not nombre:
            raise forms.ValidationError('El nombre es obligatorio.')
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        return nombre

    def clean_descripcion(self):
        desc = self.cleaned_data.get('descripcion', '') or ''
        if not desc:
            raise forms.ValidationError('La descripción es obligatoria.')
        if len(desc) > 1000:
            raise forms.ValidationError('La descripción no puede exceder 1000 caracteres.')
        return desc

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '') or ''
        tel = tel.strip()
        if not tel:
            raise forms.ValidationError('El teléfono es obligatorio.')
        # phone_validator already applied, just return stripped
        return tel
    
    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '') or ''
        direccion = direccion.strip()
        if not direccion:
            raise forms.ValidationError('La dirección es obligatoria.')
        if len(direccion) > 255:
            raise forms.ValidationError('La dirección no puede exceder 255 caracteres.')
        return direccion
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '') or ''
        email = email.strip()
        if not email:
            raise forms.ValidationError('El email es obligatorio.')
        return email

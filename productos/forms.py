from django import forms
# Asegúrate de que tu modelo Producto esté disponible
from .models import Producto, Categoria 

class ProductoForm(forms.ModelForm):
    """
    ModelForm para el modelo Producto, aplicando clases CSS de Bootstrap 
    (form-control) a todos los campos para una correcta visualización.
    """
    class Meta:
        model = Producto
        fields = ['nombre', 'precio', 'categoria', 'stock', 'descripcion', 'imagen', 'fabricante']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}), 
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}), 
            'fabricante': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = "Seleccione una categoría"
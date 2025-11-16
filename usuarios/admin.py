from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, DireccionPref, PuntoRecogidaPref


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    model = Usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Datos extra', {'fields': ('nombre', 'apellidos', 'rol', 'direccion_preferida', 'punto_recogida_pref')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos extra', {'fields': ('nombre', 'apellidos', 'rol')}),
    )


admin.site.register(DireccionPref)
admin.site.register(PuntoRecogidaPref)

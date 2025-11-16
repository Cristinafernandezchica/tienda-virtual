from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class MetodoPago(models.TextChoices):
    TARJETA = 'TAR', _('Tarjeta')
    CONTRAREEMBOLSO = 'CRD', _('Contrareembolso')


class RolUsuario(models.TextChoices):
    CLIENTE = 'CLIENTE', _('Cliente')
    ADMINISTRADOR = 'ADMIN', _('Administrador')


class Usuario(AbstractUser):
    # username, password, email, first_name, last_name ya vienen en AbstractUser
    # añadimos aliases en español y campos extra
    nombre = models.CharField(max_length=150, blank=True)
    apellidos = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    metodoPagoPref = models.CharField(
        max_length=3,
        choices=MetodoPago.choices,
        blank=True,
        null=True,
    )
    # FKs opcionales a modelos de preferencia (se definen abajo)
    direccion_preferida = models.ForeignKey(
        'DireccionPref',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_con_preferida'
    )
    punto_recogida_pref = models.ForeignKey(
        'PuntoRecogidaPref',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_con_pref'
    )
    rol = models.CharField(
        max_length=10,
        choices=RolUsuario.choices,
        default=RolUsuario.CLIENTE
    )

    USERNAME_FIELD = 'username'  # mantengo username; si quieres login por email, cambiar
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} ({self.email})"


class DireccionPref(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='direcciones')
    direccion = models.CharField(max_length=255)
    codigoPostal = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.direccion}, {self.ciudad} ({self.pais})"


class PuntoRecogidaPref(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='puntos_recogida')
    direccion = models.CharField(max_length=255)
    codigoPostal = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    horario = models.CharField(max_length=100)  # p.ej "L-V 9:00-18:00"

    def __str__(self):
        return f"{self.direccion}, {self.ciudad} ({self.horario})"

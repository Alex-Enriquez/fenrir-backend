from django.db import models
from .fields import CampoCifrado


class CategoriaContrasena(models.Model):
    """Correos, Aplicativos internos, Sistemas/Servidores, Servicios externos, etc."""
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class RegistroContrasena(models.Model):
    categoria = models.ForeignKey(CategoriaContrasena, on_delete=models.PROTECT, related_name="registros")
    empleado = models.ForeignKey(
        "empleados.Empleado", on_delete=models.SET_NULL, related_name="credenciales",
        blank=True, null=True,
    )
    plataforma = models.CharField(max_length=150)  # ej. "Microsoft 365", "Panel NAS QNAP"
    usuario = models.CharField(max_length=150, blank=True)
    correo = models.EmailField(blank=True)
    contrasena = CampoCifrado()  # se guarda cifrada automáticamente

    notas = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plataforma} ({self.categoria})"

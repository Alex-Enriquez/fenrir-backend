from django.conf import settings
from django.db import models


class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    nombre_completo = models.CharField(max_length=150, blank=True)
    puesto = models.CharField(max_length=100, blank=True)
    ha_visto_bienvenida = models.BooleanField(default=False)
    mostrar_tips = models.BooleanField(default=True)
    fecha_ultimo_tip = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

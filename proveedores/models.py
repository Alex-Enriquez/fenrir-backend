from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    servicio = models.CharField(max_length=150, blank=True)  # ej. "Internet", "Hardware", "Soporte técnico"
    contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    calificacion = models.PositiveSmallIntegerField(default=0)  # 0-5 estrellas
    notas = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

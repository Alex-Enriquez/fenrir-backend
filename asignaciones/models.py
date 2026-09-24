from django.db import models
from equipos.models import Equipo
from empleados.models import Empleado
from licencias.models import Licencia


class Asignacion(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="asignaciones")

    # Una asignación puede ser de un equipo, de una licencia, o de ambos a la vez
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="asignaciones", blank=True, null=True)
    licencia = models.ForeignKey(Licencia, on_delete=models.CASCADE, related_name="asignaciones", blank=True, null=True)

    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_devolucion = models.DateField(blank=True, null=True)  # null = sigue activa

    autorizado_por = models.CharField(max_length=150, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        recurso = self.equipo or self.licencia
        return f"{self.empleado} → {recurso}"

    @property
    def activa(self):
        return self.fecha_devolucion is None

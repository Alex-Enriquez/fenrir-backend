from django.db import models
from empleados.models import Empleado
from equipos.models import Equipo

TECNICOS = [
    ("Irving González", "Irving González"),
    ("Sammer", "Sammer"),
    ("Alexis Acosta", "Alexis Acosta"),
    ("Celia Hernández", "Celia Hernández"),
]


class Responsiva(models.Model):
    folio = models.CharField(max_length=20, unique=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="responsivas")
    fecha = models.DateField(auto_now_add=True)
    quien_entrega = models.CharField(max_length=100, choices=TECNICOS)
    observaciones = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.folio:
            ultimo = Responsiva.objects.order_by("-id").first()
            siguiente = (ultimo.id + 1) if ultimo else 1
            self.folio = f"ALX-RESP-{siguiente:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio} - {self.empleado}"


class ResponsivaItem(models.Model):
    responsiva = models.ForeignKey(Responsiva, on_delete=models.CASCADE, related_name="items")
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT, related_name="responsiva_items")
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.equipo} x{self.cantidad}"

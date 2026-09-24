from django.db import models
from proveedores.models import Proveedor

PERIODICIDADES = [
    ("mensual", "Mensual"),
    ("trimestral", "Trimestral"),
    ("semestral", "Semestral"),
    ("anual", "Anual"),
]


class ServicioContratado(models.Model):
    nombre = models.CharField(max_length=150)  # ej. "Internet Telmex", "Hosting AWS"
    tipo = models.CharField(max_length=100, blank=True)  # ej. "Internet", "Hosting", "Telefonía"
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, blank=True, null=True, related_name="servicios")
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    periodicidad = models.CharField(max_length=20, choices=PERIODICIDADES, default="mensual")
    fecha_proximo_pago = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class PagoServicio(models.Model):
    servicio = models.ForeignKey(ServicioContratado, on_delete=models.CASCADE, related_name="pagos")
    fecha = models.DateField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.servicio.nombre} - {self.fecha}"

from django.db import models


class TipoLicencia(models.Model):
    """Office 365, Adobe Creative Cloud, Antivirus, etc."""
    nombre = models.CharField(max_length=100, unique=True)
    proveedor = models.CharField(max_length=100, blank=True)  # ej. "Microsoft", "Adobe"

    def __str__(self):
        return self.nombre


class Licencia(models.Model):
    MODALIDAD_CHOICES = [
        ("suscripcion", "Suscripción"),
        ("perpetua", "Perpetua"),
    ]

    tipo = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT, related_name="licencias")
    etiqueta = models.CharField(max_length=100, blank=True)  # ej. "Finanzas", "Dirección"
    clave_producto = models.CharField(max_length=200, blank=True)  # serial/key si aplica
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default="suscripcion")

    asientos_totales = models.PositiveIntegerField(default=1)  # cuántos usuarios puede tener

    fecha_compra = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)  # null si es perpetua

    proveedor_compra = models.CharField(max_length=150, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    observaciones = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def asientos_disponibles(self):
        ocupados = self.asignaciones.count() if hasattr(self, "asignaciones") else 0
        return self.asientos_totales - ocupados

    def __str__(self):
        return f"{self.tipo} ({self.modalidad})"

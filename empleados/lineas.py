from django.db import models
from django.db.models import Q


class LineaTelefonica(models.Model):
    """Una entrada del directorio telefónico: extensión, línea fija o celular de la empresa."""
    TIPOS = [("extension", "Extensión"), ("celular", "Celular"), ("fijo", "Línea fija")]

    tipo = models.CharField(max_length=10, choices=TIPOS)
    numero = models.CharField(max_length=20)       # extensión (ej. 502) o número a 10 dígitos
    nombre = models.CharField(max_length=150)      # persona o área ("Recepción")
    empleado = models.ForeignKey("empleados.Empleado", on_delete=models.SET_NULL, null=True, blank=True, related_name="lineas_telefonicas")
    departamento = models.ForeignKey("empleados.Departamento", on_delete=models.SET_NULL, null=True, blank=True, related_name="lineas_telefonicas")
    ubicacion = models.CharField(max_length=100, blank=True)

    # Solo celulares y líneas fijas
    operador = models.CharField(max_length=50, blank=True)    # ej. Telcel
    plan = models.CharField(max_length=100, blank=True)
    chip = models.CharField("Número de chip (ICCID)", max_length=25, unique=True, null=True, blank=True)
    equipo = models.ForeignKey("equipos.Equipo", on_delete=models.SET_NULL, null=True, blank=True, related_name="lineas_telefonicas")

    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre", "numero"]
        verbose_name = "línea telefónica"
        verbose_name_plural = "directorio telefónico"
        constraints = [
            # Un número no puede estar activo dos veces; uno dado de baja se puede volver a usar.
            models.UniqueConstraint(fields=["tipo", "numero"], condition=Q(activo=True), name="linea_activa_unica"),
        ]

    def __str__(self):
        return f"{self.nombre} · {self.numero}"

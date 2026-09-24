from django.db import models


class Departamento(models.Model):
    """Área o departamento: TI, Finanzas, Ventas, RH, etc."""
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    ESTATUS_CHOICES = [
        ("activo", "Activo"),
        ("baja", "Baja"),
    ]

    nombre_completo = models.CharField(max_length=200)
    correo = models.EmailField(unique=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name="empleados")
    puesto = models.CharField(max_length=150)

    fecha_ingreso = models.DateField(blank=True, null=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default="activo")

    telefono = models.CharField(max_length=20, blank=True)
    observaciones = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo})"

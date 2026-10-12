from django.db import models


class CategoriaEquipo(models.Model):
    """Laptop, PC de escritorio, Monitor, Impresora, etc."""
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("asignado", "Asignado"),
        ("reparacion", "En reparación"),
        ("baja", "De baja"),
    ]

    categoria = models.ForeignKey(CategoriaEquipo, on_delete=models.PROTECT, related_name="equipos")
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True, blank=True, null=True)
    numero_inventario = models.CharField(max_length=50, unique=True, blank=True, null=True)
    imei = models.CharField("IMEI", max_length=20, unique=True, blank=True, null=True)

    procesador = models.CharField(max_length=150, blank=True)
    memoria_ram = models.CharField(max_length=50, blank=True)

    disco_tipo = models.CharField(
        max_length=20,
        choices=[("SSD", "SSD"), ("HDD", "HDD"), ("M2", "M.2 NVMe"), ("MIXTO", "Mixto (SSD+HDD)")],
        blank=True,
    )
    disco_capacidad = models.CharField(max_length=50, blank=True)

    sistema_operativo = models.CharField(max_length=100, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")
    ubicacion = models.CharField(max_length=100, blank=True)

    fecha_compra = models.DateField(blank=True, null=True)
    proveedor = models.CharField(max_length=150, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    garantia_hasta = models.DateField(blank=True, null=True)

    observaciones = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="equipos/", blank=True, null=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        identificador = self.numero_serie or self.imei or self.numero_inventario or "sin serie"
        return f"{self.marca} {self.modelo} ({identificador})"


class Mantenimiento(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="mantenimientos")
    fecha = models.DateField()
    descripcion = models.TextField()
    solucion = models.TextField(blank=True)
    realizado_por = models.CharField(max_length=150, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Mantenimiento {self.equipo} - {self.fecha}"

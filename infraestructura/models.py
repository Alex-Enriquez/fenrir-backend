from django.db import models

TIPOS_DISPOSITIVO = [
    ("switch", "Switch"),
    ("router", "Router"),
    ("access_point", "Access Point"),
    ("firewall", "Firewall"),
    ("servidor", "Servidor físico"),
    ("patch_panel", "Patch Panel"),
    ("otro", "Otro"),
]

ESTADOS_DISPOSITIVO = [
    ("operativo", "Operativo"),
    ("mantenimiento", "En mantenimiento"),
    ("fuera_de_linea", "Fuera de línea"),
]


class Rack(models.Model):
    nombre = models.CharField(max_length=150)  # ej. "Rack Servidores - Piso 1"
    ubicacion = models.CharField(max_length=150, blank=True)
    altura_u = models.PositiveIntegerField(default=42)

    def __str__(self):
        return self.nombre


class DispositivoRed(models.Model):
    tipo = models.CharField(max_length=20, choices=TIPOS_DISPOSITIVO, default="switch")
    nombre = models.CharField(max_length=150)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    ip_gestion = models.CharField(max_length=50, blank=True)

    rack = models.ForeignKey(Rack, on_delete=models.SET_NULL, blank=True, null=True, related_name="dispositivos")
    posicion_u = models.PositiveIntegerField(blank=True, null=True)  # posición inicial en el rack
    altura_u = models.PositiveIntegerField(default=1)  # cuántas U's ocupa

    garantia_hasta = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_DISPOSITIVO, default="operativo")
    numero_puertos = models.PositiveIntegerField(default=0)  # solo relevante para switches
    notas = models.TextField(blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class PuertoRed(models.Model):
    ESTADOS_PUERTO = [
        ("libre", "Libre"),
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    dispositivo = models.ForeignKey(DispositivoRed, on_delete=models.CASCADE, related_name="puertos")
    numero = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, default="RJ45")
    velocidad = models.CharField(max_length=20, blank=True)  # ej. "1G", "10G"
    estado = models.CharField(max_length=20, choices=ESTADOS_PUERTO, default="libre")
    conectado_a = models.CharField(max_length=150, blank=True)
    vlan = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"Puerto {self.numero} - {self.dispositivo.nombre}"

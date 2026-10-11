from django.db import models
from empleados.models import Empleado
from equipos.models import Equipo

TECNICOS = [
    ("Irving Sammer González", "Irving Sammer González"),
    ("Alexis Acosta", "Alexis Acosta"),
    ("Celia Hernández", "Celia Hernández"),
]


class ContadorResponsiva(models.Model):
    valor = models.PositiveIntegerField(default=0)

    @classmethod
    def siguiente(cls):
        contador, _ = cls.objects.get_or_create(pk=1)
        while True:
            contador.valor += 1
            # si ese folio ya existe (responsivas creadas con la lógica anterior), se salta
            if not Responsiva.objects.filter(folio=f"ALX-RESP-{contador.valor:05d}").exists():
                break
        contador.save()
        return contador.valor

    @classmethod
    def liberar_si_es_el_ultimo(cls, numero):
        contador, _ = cls.objects.get_or_create(pk=1)
        if contador.valor == numero:
            contador.valor -= 1
            contador.save()


class Responsiva(models.Model):
    folio = models.CharField(max_length=20, unique=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="responsivas")
    fecha = models.DateField(auto_now_add=True)
    quien_entrega = models.CharField(max_length=100, choices=TECNICOS)
    observaciones = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.folio:
            numero = ContadorResponsiva.siguiente()
            self.folio = f"ALX-RESP-{numero:05d}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            numero = int(self.folio.split("-")[-1])
        except (ValueError, AttributeError):
            numero = None
        resultado = super().delete(*args, **kwargs)
        if numero is not None:
            ContadorResponsiva.liberar_si_es_el_ultimo(numero)
        return resultado

    def __str__(self):
        return f"{self.folio} - {self.empleado}"


class ResponsivaItem(models.Model):
    responsiva = models.ForeignKey(Responsiva, on_delete=models.CASCADE, related_name="items")
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT, related_name="responsiva_items")
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.equipo} x{self.cantidad}"

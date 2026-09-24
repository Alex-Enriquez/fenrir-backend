from django.contrib import admin
from .models import ServicioContratado, PagoServicio


class PagoServicioInline(admin.TabularInline):
    model = PagoServicio
    extra = 0


@admin.register(ServicioContratado)
class ServicioContratadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "proveedor", "costo", "periodicidad", "fecha_proximo_pago", "activo")
    inlines = [PagoServicioInline]

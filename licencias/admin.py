from django.contrib import admin
from .models import TipoLicencia, Licencia


@admin.register(TipoLicencia)
class TipoLicenciaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "proveedor")


@admin.register(Licencia)
class LicenciaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "modalidad", "asientos_totales", "fecha_vencimiento")
    list_filter = ("modalidad", "tipo")

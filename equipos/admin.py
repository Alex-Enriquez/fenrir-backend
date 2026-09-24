from django.contrib import admin
from .models import CategoriaEquipo, Equipo, Mantenimiento


@admin.register(CategoriaEquipo)
class CategoriaEquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("marca", "modelo", "numero_serie", "categoria", "estado", "ubicacion")
    list_filter = ("estado", "categoria", "disco_tipo")
    search_fields = ("marca", "modelo", "numero_serie", "numero_inventario")


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ("equipo", "fecha", "realizado_por")

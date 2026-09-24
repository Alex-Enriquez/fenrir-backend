from django.contrib import admin
from .models import Asignacion


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ("empleado", "equipo", "licencia", "fecha_asignacion", "fecha_devolucion", "activa")
    list_filter = ("fecha_asignacion",)
    search_fields = ("empleado__nombre_completo", "equipo__numero_serie")

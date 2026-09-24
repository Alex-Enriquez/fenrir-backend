from django.contrib import admin
from .models import Departamento, Empleado


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "correo", "departamento", "puesto", "estatus")
    list_filter = ("departamento", "estatus")
    search_fields = ("nombre_completo", "correo")

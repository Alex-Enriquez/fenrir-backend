from django.contrib import admin
from .models import CategoriaContrasena, RegistroContrasena


@admin.register(CategoriaContrasena)
class CategoriaContrasenaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)


@admin.register(RegistroContrasena)
class RegistroContrasenaAdmin(admin.ModelAdmin):
    list_display = ("plataforma", "categoria", "usuario", "correo", "fecha_actualizacion")
    list_filter = ("categoria",)
    search_fields = ("plataforma", "usuario", "correo")

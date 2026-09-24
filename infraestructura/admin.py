from django.contrib import admin
from .models import Rack, DispositivoRed, PuertoRed


class PuertoRedInline(admin.TabularInline):
    model = PuertoRed
    extra = 0


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion", "altura_u")


@admin.register(DispositivoRed)
class DispositivoRedAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "rack", "posicion_u", "altura_u", "estado")
    inlines = [PuertoRedInline]

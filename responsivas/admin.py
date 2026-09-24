from django.contrib import admin
from .models import Responsiva, ResponsivaItem


class ResponsivaItemInline(admin.TabularInline):
    model = ResponsivaItem
    extra = 1


@admin.register(Responsiva)
class ResponsivaAdmin(admin.ModelAdmin):
    list_display = ("folio", "empleado", "fecha", "quien_entrega")
    readonly_fields = ("folio",)
    inlines = [ResponsivaItemInline]
